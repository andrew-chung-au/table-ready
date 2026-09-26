# AWS Deployment Plan — Phases 4–6

This document is a step-by-step implementation guide for taking Table Ready from "runs via `docker compose up`" to "runs on AWS behind a real CI/CD pipeline." It's written for hand implementation (by you, possibly with AI chat help), not for an agent to execute unattended — every step explains *why*, not just *what to type*, and flags what to verify and what commonly breaks.

It picks up at **Phase 4**; phases 1–3 (in-memory prototype → SQLite → Postgres/Docker/Alembic, per the README's history section) are already done. This doc does not renumber them.

It is distinct from `docs/deployment.md`, `docs/testing.md`, and `docs/release-process.md`, which are currently empty placeholders (0 bytes each) — those get filled in **after** Phases 4 and 5 are actually built, documenting what was really shipped rather than what was planned. Phase 6 below explains what will need to go into `release-process.md` specifically, but doesn't write it.

---

## 0. What this plan found when it inspected the repo

A few things worth knowing before you start, because they shape decisions below:

- **No `.github/workflows/` exists.** There's nothing to migrate away from — Phase 5 is additive, not a replacement of an existing GitHub Actions setup.
- **No `infra/` directory exists yet.** The README already anticipates it (§ "Immediate next step: AWS deployment") and says explicitly it doesn't exist yet — confirmed. Phase 4 creates it.
- **No `/health` endpoint exists.** `make e2e` currently polls `GET /api/venue` as its readiness check. See § 4.1 for whether to keep using that or add a dedicated endpoint (short answer: add a dedicated one).
- **`E2E_BASE_URL` already exists** as an env var in `e2e/playwright.config.ts`, defaulting to `http://localhost:8091`. This means pointing the Playwright suite at a real deployed URL instead of local docker-compose requires zero code changes — just set the env var. See § 5.3 for where this fits in the pipeline (it doesn't move — Playwright still runs against the local Compose stack in the Build stage, per the structure specified for this pipeline; `E2E_BASE_URL` is what makes it possible to *also* point it at staging later if you want a second, heavier gate, but that's not part of this plan).
- **`backend/config.py`'s `DEFAULT_PORT`/`PORT` env var is dead code.** It's computed but never used — the actual serving port is hardcoded to `8091` in both the `Dockerfile` CMD and `docker-compose.yml`. Treat `8091` as fixed for ALB target group / health check configuration; don't expect a `PORT` env var to change it without a code change.
- **`FRONTEND_DIST_DIR` needs no override in production.** The `Dockerfile` already bakes `ENV FRONTEND_DIST_DIR=/app/frontend_dist` into the image, matching where the frontend build output is copied. Nothing to set in the ECS task definition for this.
- **The app makes no outbound AWS API calls** (no `boto3`, no `AWS_*` env vars anywhere in `backend/`). The ECS **task role** (as opposed to the task *execution* role, which is different and does need permissions — see § 4.4) can stay empty.

---

## Prerequisites

Do these once, before touching Phase 4.

### 1. AWS account and least-privilege IAM for yourself

Don't do this work as the account root user. Create (or have created for you) an IAM identity scoped to what this project needs, and use that day to day:

```bash
# As an account admin (one-time, ideally via the AWS console or an existing
# bootstrap process — this is the one place root/admin credentials are
# appropriate):
aws iam create-user --user-name table-ready-deployer
aws iam create-group --group-name table-ready-deployers
aws iam add-user-to-group --user-name table-ready-deployer --group-name table-ready-deployers
```

Attach a policy to the group scoped to the services this project touches: CloudFormation, ECS, ECR, RDS, EC2 (VPC/security groups), IAM (to create the *other*, narrower roles below — this is the one place your own user needs `iam:CreateRole`/`iam:AttachRolePolicy`, scoped with a permissions boundary if you want to be strict about it), Secrets Manager, CodePipeline, CodeBuild, CodeStar Connections, S3 (artifact bucket), SNS (approval notifications), and CloudWatch Logs. Managed policies like `AWSCloudFormationFullAccess` + `AmazonECS_FullAccess` + `AmazonEC2FullAccess` + `IAMFullAccess` are the fast path to get moving; tightening this into a real least-privilege policy is worth doing once you know exactly which actions you use (the actual `aws cloudformation deploy` / `aws ecs` commands throughout this doc are your inventory).

Verify:
```bash
aws sts get-caller-identity   # should show the table-ready-deployer user, not root
```

### 2. CodeStar Connection to this GitHub repo

CodePipeline can't reach a private GitHub repo on its own — it needs a **CodeStar Connection**, which is a GitHub App installed on your GitHub account/org, authorized once through the console (this step genuinely can't be scripted — the GitHub OAuth handshake requires a browser).

```bash
aws codestar-connections create-connection \
  --provider-type GitHub \
  --connection-name table-ready-github
```

This returns a connection ARN with status `PENDING`. Go to the AWS Console → Developer Tools → Settings → Connections, find `table-ready-github`, click **Update pending connection**, and complete the GitHub App install/authorization flow, pointing it at the `table-ready` repo (or your whole account if you want it reusable). After that, the connection's status flips to `AVAILABLE`:

```bash
aws codestar-connections get-connection --connection-arn <CONNECTION_ARN>
# ConnectionStatus should be AVAILABLE, not PENDING
```

Keep the ARN — Phase 5's pipeline template takes it as a parameter.

### 3. Local tooling

- `aws` CLI v2, configured with the `table-ready-deployer` credentials (`aws configure` or an SSO profile).
- `docker` (already needed locally; CodeBuild will also need Docker-in-Docker, see § 5.3).
- Nothing else new — `uv`, `bun`, and Docker Compose you already have for local dev.

---

## Phase 4: AWS Deployment & Environments

### 4.1 Add a dedicated health endpoint

`make e2e` today polls `GET /api/venue` as its readiness gate, and it's tempting to keep reusing it for the ALB health check and pipeline smoke test too — one less thing to build. But recommend **adding a small dedicated `/health` endpoint instead**:

- `/api/venue` returns a full business payload and depends on seed data existing (`seed_if_empty` on startup). It's fine as a *local dev* readiness proxy, but using it as the ALB's health check means ALB target health becomes coupled to venue business logic — a future change to venue seeding or schema could make the ALB start flapping targets for reasons that have nothing to do with "is the process up and can it reach the database."
- A dedicated endpoint is a few lines, decouples ops/infra concerns from the API surface, and is the thing you actually want the ALB and the pipeline's smoke-test stage hitting.
- Leave `make e2e` and its `/api/venue` poll alone — no reason to touch working local tooling.

Add (not yet applied — this is what to add in Phase 4):

```python
# backend/routers/health.py
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.deps import get_repository

router = APIRouter(tags=["health"])


@router.get("/health")
def health(repo=Depends(get_repository)):
    repo.session.execute(text("SELECT 1"))
    return {"status": "ok"}
```

Register it in `backend/main.py` alongside the other routers (`api_router.include_router(health.router)`), so it lands at `/api/health`. Use that full path (`/api/health`) consistently as the target group health check path, the ECS Express Mode health check, and the smoke-test URL in Phase 5 — using `/api/health` rather than a bare `/health` keeps every ops-facing check behind the same `/api` prefix as the rest of the routed API, and avoids a collision with the SPA catch-all route (`serve_frontend` in `main.py` greedily matches `/{full_path:path}` for anything not under `/api/`).

**Verify:** after deploying (§ 4.5), `curl -s https://<alb-dns>/api/health` returns `{"status":"ok"}` with a `200`.

### 4.2 ECR repository

One ECR repo, shared across staging and production — they're distinguished by image *tag*, not by separate repos. This matches decision #4 (same template, different parameter values) applied one level down: same repo, different tags.

```bash
aws ecr create-repository \
  --repository-name table-ready \
  --image-scanning-configuration scanOnPush=true \
  --image-tag-mutability IMMUTABLE
```

`IMMUTABLE` tags matter here: Phase 6's rollback story depends on being able to trust that a tag (or digest) you deployed last week still points at exactly what you tested last week, not something silently overwritten by a later push reusing the same tag.

Tag images by **git commit SHA** (`table-ready:<short-sha>`), not `latest` or a version number you'd have to remember to bump — CodeBuild has `$CODEBUILD_RESOLVED_SOURCE_VERSION` available for exactly this. This also makes "what's running in production right now" and "what's the last known-good image" both answerable by looking up a commit, which is what Phase 6's rollback procedure leans on.

**Verify:**
```bash
aws ecr describe-repositories --repository-names table-ready
```

### 4.3 CloudFormation template design (`infra/app-stack.yaml`)

This is the parameterized template decision #4 calls for: one template, deployed twice (staging, production) with different parameter values, and reusable again later for a second customer's isolated stack.

**Isolation model:** each stack instance gets its **own VPC**, not a shared one — this matches the "isolated stack per customer" delivery model at the network level too, not just the app level. A small VPC costs nothing extra to create per-stack, and it means a staging misconfiguration (an overly permissive security group, say) can't accidentally expose production, because they're not in the same network.

**Cost-saving subnet layout, worth calling out explicitly:** put both the ALB *and* the Fargate tasks in **public subnets**, with the tasks assigned public IPs (`AssignPublicIp: ENABLED`). This sounds counter to "least privilege," but it isn't — the security group on the task, not subnet placement, is what actually gates inbound traffic (only the ALB's security group is allowed to reach the task's container port; the public IP doesn't change that). What it buys you: the tasks can reach ECR and CloudWatch Logs without a NAT Gateway, which costs about $32–35/month per AZ just for the gateway to exist, before any data-transfer charges — real money for a "small business tool" that this decision set is explicitly trying to keep cheap. RDS goes in separate subnets with no route to an internet gateway at all (a real "private" subnet, via a DB Subnet Group), since it never needs outbound internet access and there's no cost tradeoff to make there. If you'd rather have fully private, no-public-IP tasks behind a NAT Gateway (more conventional "prod-grade" default), that's a legitimate choice too — just note it costs more per environment, and with two environments (soon three-plus) that cost multiplies.

**Parameters:**

| Parameter | Example (staging) | Example (production) | Purpose |
|---|---|---|---|
| `EnvironmentName` | `staging` | `production` | Used in resource names/tags; also what Phase 5's pipeline passes to distinguish targets |
| `ImageTag` | `<git-sha>` | `<git-sha>` | Which ECR image tag the service runs |
| `DesiredCount` | `1` | `1` | Fixed task count — decision #3, no autoscaling for public demand |
| `MaxCount` | `1` | `2` | Small ceiling, not internet-scale autoscaling |
| `DBInstanceClass` | `db.t4g.micro` | `db.t4g.micro` (or one size up) | RDS sizing |
| `DBAllocatedStorage` | `20` | `20` | GB, gp3 |

**Core resources** (grouped by concern — write these as one template, this is the logical breakdown):

**Networking:** `AWS::EC2::VPC`, 2 public subnets (different AZs, for ALB + Fargate — Fargate services require ≥2 subnets across AZs even at `DesiredCount: 1`, for the platform to be able to replace an unhealthy task), 2 isolated private subnets (RDS, via `AWS::RDS::DBSubnetGroup`), an Internet Gateway + public route table for the public subnets. No NAT Gateway, per the cost note above.

**Security groups:**
- ALB SG: inbound 443 (and 80 if you're not doing TLS yet — see note below) from `0.0.0.0/0`.
- Task SG: inbound `8091` (the fixed app port, § 0) from the ALB SG only.
- DB SG: inbound `5432` from the task SG only.

**IAM roles** (created by this template, distinct from your own IAM user in Prerequisites §1):
- **Task execution role** (`AWS::IAM::Role`, trust policy for `ecs-tasks.amazonaws.com`): needs `ecr:GetAuthorizationToken`, `ecr:BatchGetImage`, `ecr:GetDownloadUrlForLayer` (to pull the image), `logs:CreateLogStream`/`logs:PutLogEvents` (the `awslogs` driver), and `secretsmanager:GetSecretValue` scoped to the one `DATABASE_URL` secret's ARN (ECS resolves `secrets` entries in the task definition using *this* role, at task launch — not the task role). AWS ships `AmazonECSTaskExecutionRolePolicy` as a managed policy covering the ECR/logs part; attach that plus an inline policy for the Secrets Manager permission scoped to the specific secret ARN.
- **Task role**: attach no policies. The app makes no AWS API calls at runtime (§ 0). Express Mode likely still wants a task role ARN supplied even if it's a no-op role — that's fine, it's cheap to create and correct to leave empty rather than over-granting "just in case."
- **Infrastructure role** for Express Mode itself: a role with the `AmazonECSInfrastructureRoleforExpressGatewayServices` AWS-managed policy attached, trusting the ECS service principal. This is what lets Express Mode provision/manage the ALB, target group, and security groups on your behalf.
  > ⚠️ The exact trust-policy principal Express Mode expects for this role isn't something to guess at from memory — when you create it, check the current Express Mode quickstart/console flow (or `aws ecs` CLI help) for the literal trust policy it expects. Creating the role by hand with a slightly wrong trust policy is a plausible source of a confusing first-deploy failure.

**Database:** `AWS::RDS::DBInstance`, PostgreSQL, single-AZ (`MultiAZ: false` — decision #6), `BackupRetentionPeriod: 7` (this single property is what turns on both automated backups *and* point-in-time recovery — there's no separate PITR toggle), `StorageType: gp3`, not publicly accessible, in the DB subnet group above. Master password: generate via a `AWS::SecretsManager::Secret` with `GenerateSecretString`, then reference it in the DB instance's `MasterUserPassword` property using a Secrets Manager dynamic reference (`{{resolve:secretsmanager:...}}`) rather than a plaintext parameter — this is a standard, well-documented CloudFormation pattern for exactly this purpose.

**The `DATABASE_URL` secret:** the app wants one connection-string env var, but ECS task definition `secrets` entries map one container env var to one secret's value (or one JSON key within it) — there's no string-templating across multiple secrets at the task-definition level. The practical fix is a *second* secret that holds the fully-assembled URL:

```yaml
DatabaseUrlSecret:
  Type: AWS::SecretsManager::Secret
  Properties:
    Name: !Sub '${EnvironmentName}-table-ready-database-url'
    SecretString: !Sub
      - 'postgresql://{{resolve:secretsmanager:${DbCredentialsSecret}:SecretString:username}}:{{resolve:secretsmanager:${DbCredentialsSecret}:SecretString:password}}@${DbEndpoint}:5432/waitlist'
      - DbEndpoint: !GetAtt DbInstance.Endpoint.Address
```

> ⚠️ Combining `Fn::Sub` with `{{resolve:secretsmanager:...}}` dynamic references like this is a documented pattern for building connection strings from an auto-generated password, and should work, but verify it resolves the way you expect in your account/region before relying on it — if it doesn't, the fallback is a small custom resource (Lambda-backed) that reads both values and writes the assembled URL as a third secret.

The ECS task definition then references `DatabaseUrlSecret`'s ARN directly for the `DATABASE_URL` container env var. No app code changes needed — `backend/config.py` already just reads `DATABASE_URL` from the environment.

**Compute — the Express Mode question:**

Decision #2 settles *that* this is ECS Express Mode; here's what to actually write. Express Mode's whole pitch is that you give it an image + the two roles above and it provisions the cluster, task definition, Fargate service, ALB, target group, listener, and security groups for you. What isn't settled in this plan, because it isn't something to guess at: **whether that provisioning surfaces as a distinct CloudFormation resource type**, or whether it's currently a console/CLI-only quickstart experience layered on top of standard `AWS::ECS::*` resources.

> ⚠️ Before writing the template, check the current `AWS::ECS` CloudFormation resource reference for anything Express-Mode-specific. If it exists, it's very likely less code than the option below and worth using.

Either way, here's the fallback that's guaranteed to work, because decision #2 itself is explicit that Express Mode is "standard ECS underneath" — meaning hand-authoring the equivalent standard resources produces a functionally identical result, just with more template lines:

- `AWS::ECS::Cluster`
- `AWS::ECS::TaskDefinition` — Fargate, `0.5 vCPU` / `1 GB` (small, matches decision #3's sizing philosophy), the execution role and task role from above, one container definition: image `<ecr-repo-uri>:<ImageTag>`, port `8091`, `secrets: [{Name: DATABASE_URL, ValueFrom: <DatabaseUrlSecret ARN>}]`, `logConfiguration` using `awslogs` into a `AWS::Logs::LogGroup` you also create.
- `AWS::ECS::Service` — `LaunchType: FARGATE`, `DesiredCount: !Ref DesiredCount`, the task SG + public subnets, `LoadBalancers` pointing at the target group below, `HealthCheckGracePeriodSeconds` generous enough for the app's startup (DB connect + seed check) — a minute is a reasonable starting point.
- `AWS::ElasticLoadBalancingV2::LoadBalancer` (internet-facing, public subnets, ALB SG), `::TargetGroup` (port `8091`, health check path `/api/health` from § 4.1, protocol HTTP), `::Listener` (port 443 with an ACM cert if you're doing TLS — see below — otherwise port 80 for the default AWS-provided URL).
- `AWS::ApplicationAutoScaling::ScalableTarget` + `::ScalingPolicy` — min `1`, max `!Ref MaxCount`. This exists mainly so ECS can replace an unhealthy task, not to handle traffic spikes; decision #3 is explicit that real load here is bounded by one restaurant's foot traffic.

**TLS / custom domain:** per decision #2, the default AWS-provided ALB DNS name is sufficient for this project's scope. That means HTTP-only (port 80) is fine to start — a Route 53 hosted zone + ACM certificate + HTTPS listener is a legitimate later addition (mention it, don't build it now).

Save this as `infra/app-stack.yaml`.

### 4.4 First deploy of each stack

There's a real chicken-and-egg problem on a brand-new stack: the service can't start successfully until migrations have run (the app's `seed_if_empty` call on startup queries tables that don't exist yet on an empty database), but the migration task needs the RDS instance and networking to exist first, and *that* needs the CloudFormation stack to have finished creating. So the very first deploy of each environment is a two-step manual sequence (Phase 5's pipeline automates this ordering for every deploy *after* this one):

```bash
# 1. Create the stack — RDS, networking, ECS service, everything above.
#    The service will come up initially with 0 healthy tasks and keep
#    restarting/crash-looping until step 2 runs. That's expected, not a
#    failure to debug.
aws cloudformation deploy \
  --template-file infra/app-stack.yaml \
  --stack-name table-ready-staging \
  --parameter-overrides \
      EnvironmentName=staging \
      ImageTag=<first-git-sha-you-built> \
      DesiredCount=1 \
      MaxCount=1 \
  --capabilities CAPABILITY_NAMED_IAM
```

```bash
# 2. Run the migration as a one-off task against the task definition the
#    stack just created, BEFORE the service's tasks manage to come up
#    healthy on their own (they won't, until this runs — but do this
#    promptly rather than relying on that).
aws ecs run-task \
  --cluster table-ready-staging \
  --task-definition table-ready-staging \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[<subnet-id-1>,<subnet-id-2>],securityGroups=[<task-sg-id>],assignPublicIp=ENABLED}" \
  --overrides '{"containerOverrides":[{"name":"app","command":["uv","run","--no-sync","alembic","upgrade","head"]}]}'
```

Wait for it to finish and check the exit code before assuming success:

```bash
TASK_ARN=<from the run-task output>
aws ecs wait tasks-stopped --cluster table-ready-staging --tasks "$TASK_ARN"
aws ecs describe-tasks --cluster table-ready-staging --tasks "$TASK_ARN" \
  --query 'tasks[0].containers[0].exitCode'
# must be 0 — anything else, go read the container's CloudWatch Logs
# before touching anything else
```

Once the migration task exits `0`, the service's existing tasks (which have been crash-looping) will start passing health checks on their own within a task-definition-restart cycle, or you can force it:

```bash
aws ecs update-service --cluster table-ready-staging --service table-ready-staging --force-new-deployment
```

Repeat both steps for production, with `EnvironmentName=production`, `MaxCount=2`, and a separate `--stack-name table-ready-production`.

> ⚠️ **On `ecs:RunTask` against an Express-Mode-managed task definition:** decision #2 states Express Mode supports normal ECS APIs including RunTask, and that's the basis this whole migration mechanism (here and in Phase 5) is built on. Whether Express Mode imposes any additional restriction on *which* task definition revisions or network configurations `RunTask` will accept (for instance, if it locks the service's networking config in a way that requires the RunTask call to mirror it exactly) isn't something to state as settled — confirm against current AWS documentation, and expect to test this specific step in staging first, before wiring it into the production side of the Phase 5 pipeline.

**Verify each stack:**

```bash
aws cloudformation describe-stacks --stack-name table-ready-staging \
  --query 'Stacks[0].StackStatus'
# CREATE_COMPLETE

aws cloudformation describe-stacks --stack-name table-ready-staging \
  --query 'Stacks[0].Outputs'
# should include the ALB DNS name — export it as a stack Output if you
# haven't already; Phase 5's smoke test needs it

aws ecs describe-services --cluster table-ready-staging --services table-ready-staging \
  --query 'services[0].{running:runningCount,desired:desiredCount}'
# running should equal desired (1)

curl -s -o /dev/null -w '%{http_code}\n' https://<alb-dns-name>/api/health
# 200
```

**Common pitfalls at this stage:**
- Forgetting step 2 and concluding the stack "failed" when the service is just crash-looping on a missing schema — check CloudWatch Logs for the actual container error before assuming CloudFormation did something wrong.
- RDS taking several minutes to become available after stack creation starts — `cloudformation deploy` waits for this correctly, but if you're impatient and run `run-task` too early it'll fail to connect; just retry.
- Security group ordering: if you reference the task SG in the DB SG's ingress rule and vice versa in the same template, you can hit a circular-dependency error — break the cycle by adding the cross-referencing ingress rule as a separate `AWS::EC2::SecurityGroupIngress` resource rather than inline on both groups.

---

## Phase 5: CI/CD Pipeline & Smoke Testing

One `AWS::CodePipeline::Pipeline`, defined in `infra/pipeline.yaml` (a separate template from `infra/app-stack.yaml`, deployed once, not per-environment — it *targets* both the staging and production app stacks from Phase 4, but the pipeline itself isn't duplicated). Sequential stages, each gating the next:

```
Source → Test → Build → Deploy-Staging → Smoke-Test-Staging
       → Manual Approval → Deploy-Production → Smoke-Test-Production
```

### 5.1 Source stage

A CodeStarSourceConnection action using the connection ARN from Prerequisites §2, triggering on push to `main`:

```yaml
- Name: Source
  Actions:
    - Name: GitHubSource
      ActionTypeId:
        Category: Source
        Owner: AWS
        Provider: CodeStarSourceConnection
        Version: '1'
      Configuration:
        ConnectionArn: !Ref CodeStarConnectionArn
        FullRepositoryId: <github-org>/table-ready
        BranchName: main
      OutputArtifacts:
        - Name: SourceOutput
```

### 5.2 Test stage — two parallel CodeBuild actions

CodePipeline runs actions within a stage concurrently by default (no fan-out configuration needed) — give both actions the same `RunOrder` and they execute in parallel, with the stage only advancing once both succeed:

```yaml
- Name: Test
  Actions:
    - Name: BackendTests
      RunOrder: 1
      ActionTypeId: {Category: Build, Owner: AWS, Provider: CodeBuild, Version: '1'}
      Configuration: {ProjectName: !Ref BackendTestProject}
      InputArtifacts: [{Name: SourceOutput}]
    - Name: FrontendTests
      RunOrder: 1
      ActionTypeId: {Category: Build, Owner: AWS, Provider: CodeBuild, Version: '1'}
      Configuration: {ProjectName: !Ref FrontendTestProject}
      InputArtifacts: [{Name: SourceOutput}]
```

**BackendTestProject** buildspec — just `uv run pytest`, matching `make test-backend` exactly (default `addopts = "-m 'not integration'"` in `pyproject.toml` already excludes the Docker-dependent integration tests, appropriately — those belong in the Build stage below where Docker is actually available):

```yaml
version: 0.2
phases:
  install:
    commands:
      - curl -LsSf https://astral.sh/uv/install.sh | sh
      - export PATH="$HOME/.local/bin:$PATH"
  build:
    commands:
      - uv sync
      - uv run pytest
```

**FrontendTestProject** buildspec — `bun test`, matching `make test-frontend` (runs `vitest run` per `frontend/package.json`):

```yaml
version: 0.2
phases:
  install:
    commands:
      - curl -fsSL https://bun.sh/install | bash
      - export PATH="$HOME/.bun/bin:$PATH"
  build:
    commands:
      - cd frontend && bun install && bun test
```

Both are small, standard-compute CodeBuild environments — no Docker needed here.

### 5.3 Build stage — Compose stack, integration tests, e2e, then build+push

This is the heaviest stage and needs a CodeBuild project running in **privileged mode** (Docker-in-Docker — CodeBuild's own container needs to run `docker compose` and Playwright's Chromium inside itself) with a compute size bumped up from the Test stage's — enough for Postgres + the app + a real browser concurrently (`BUILD_GENERAL1_MEDIUM` is a reasonable starting point; watch for OOM in the build logs and size up if Chromium or Postgres get killed).

Buildspec, mirroring exactly what `make e2e` does today plus the Postgres integration tests, then the actual image build/push:

```yaml
version: 0.2
phases:
  install:
    runtime-versions:
      nodejs: 22
    commands:
      - curl -LsSf https://astral.sh/uv/install.sh | sh
      - export PATH="$HOME/.local/bin:$PATH"
  pre_build:
    commands:
      - docker compose up -d --build
      - |
        i=0; until curl -sf http://localhost:8091/api/venue > /dev/null 2>&1; do
          i=$((i+1)); [ "$i" -ge 60 ] && { echo "app never became ready"; docker compose logs; exit 1; }
          sleep 2
        done
      - uv sync
      - uv run pytest tests/integration -m integration
      - cd e2e && npm install && npx playwright install --with-deps chromium && npm test && cd ..
      - docker compose down
      - aws ecr get-login-password --region "$AWS_DEFAULT_REGION" | docker login --username AWS --password-stdin "$ECR_REPO_URI"
  build:
    commands:
      - docker build -t "$ECR_REPO_URI:$CODEBUILD_RESOLVED_SOURCE_VERSION" .
  post_build:
    commands:
      - docker push "$ECR_REPO_URI:$CODEBUILD_RESOLVED_SOURCE_VERSION"
      - printf '{"imageTag":"%s"}' "$CODEBUILD_RESOLVED_SOURCE_VERSION" > image-tag.json
artifacts:
  files:
    - image-tag.json
```

`image-tag.json` becomes the output artifact carrying the exact tag downstream — Deploy-Staging and Deploy-Production both read this rather than recomputing it, so the thing that gets promoted to production after Manual Approval is provably the same artifact that passed every gate, not a rebuild.

`docker compose down` even on the happy path (with `set -e` implicit in CodeBuild's phase failure handling, a failed test will stop the buildspec before reaching `post_build`, which is fine — but consider whether you want a `finally`-style cleanup; unlike `make e2e`'s `Makefile` target, a plain buildspec doesn't have that shell trap by default, so a failed integration test here can leak the compose stack inside the ephemeral CodeBuild container. Since CodeBuild containers are torn down after each build regardless, this is low-stakes, but worth a `docker compose down || true` as a `finally` in the `post_build` phase if you want it explicit).

### 5.4 Deploy-Staging — migrate, then update the service

One CodeBuild action, no Docker needed here (pure AWS CLI):

```yaml
version: 0.2
phases:
  build:
    commands:
      - IMAGE_TAG=$(node -pe "require('./image-tag.json').imageTag")
      - |
        TASK_ARN=$(aws ecs run-task \
          --cluster table-ready-staging \
          --task-definition table-ready-staging \
          --launch-type FARGATE \
          --network-configuration "awsvpcConfiguration={subnets=[$STAGING_SUBNETS],securityGroups=[$STAGING_TASK_SG],assignPublicIp=ENABLED}" \
          --overrides "{\"containerOverrides\":[{\"name\":\"app\",\"command\":[\"uv\",\"run\",\"--no-sync\",\"alembic\",\"upgrade\",\"head\"]}]}" \
          --query 'tasks[0].taskArn' --output text)
      - aws ecs wait tasks-stopped --cluster table-ready-staging --tasks "$TASK_ARN"
      - |
        EXIT_CODE=$(aws ecs describe-tasks --cluster table-ready-staging --tasks "$TASK_ARN" \
          --query 'tasks[0].containers[0].exitCode' --output text)
        [ "$EXIT_CODE" = "0" ] || { echo "migration failed, exit code $EXIT_CODE"; exit 1; }
      - aws ecs update-service --cluster table-ready-staging --service table-ready-staging \
          --task-definition table-ready-staging --force-new-deployment
      - aws ecs wait services-stable --cluster table-ready-staging --services table-ready-staging
```

`services-stable` is the important last line — it makes this action (and therefore the pipeline) actually wait for the new tasks to pass health checks before declaring success, rather than reporting green the instant the API call to update the service returns.

Note this action's new task definition revision needs to reference the *new* image tag — either register a fresh task definition revision as part of this step (`aws ecs register-task-definition` with the updated image URI, then reference that revision in both the `run-task` migration call and the `update-service` call), or have the CloudFormation stack itself track `ImageTag` as a parameter you `aws cloudformation deploy` with an updated value before the ECS calls. The CloudFormation-parameter approach is more consistent with decision #4's "same template, different parameter values" philosophy and keeps the task definition's source of truth in one place — prefer it over registering task definitions out-of-band from CodeBuild.

### 5.5 Smoke-Test-Staging

Small, fast, fails the pipeline on anything but 200:

```yaml
version: 0.2
phases:
  build:
    commands:
      - STATUS=$(curl -s -o /dev/null -w '%{http_code}' "https://$STAGING_ALB_DNS/api/health")
      - '[ "$STATUS" = "200" ] || { echo "smoke test got $STATUS"; exit 1; }'
```

`STAGING_ALB_DNS` comes from the staging stack's CloudFormation Output (§ 4.4) — wire it in as a CodeBuild environment variable on this project, or fetch it live with `aws cloudformation describe-stacks --query 'Stacks[0].Outputs[?OutputKey==`AlbDnsName`].OutputValue'` at the top of the buildspec if you'd rather not hardcode it and risk it drifting after a stack update.

### 5.6 Manual Approval

CodePipeline's built-in `Manual` approval action type, with an SNS topic so it's not silently missed:

```yaml
- Name: ManualApproval
  Actions:
    - Name: PromoteToProduction
      ActionTypeId: {Category: Approval, Owner: AWS, Provider: Manual, Version: '1'}
      Configuration:
        NotificationArn: !Ref ApprovalTopicArn
        CustomData: "Staging smoke test passed for this commit. Approve to deploy to production."
```

Create the SNS topic in `infra/pipeline.yaml` too, with an email subscription (`AWS::SNS::Subscription`, `Protocol: email`, your address) — subscriptions need one manual confirmation click from the inbox the first time, same category of one-time manual step as the CodeStar Connection.

The pipeline genuinely pauses here — nothing rebuilds. Approving just unblocks the next stage, which references the same `image-tag.json` artifact from the Build stage.

### 5.7 Deploy-Production and Smoke-Test-Production

Identical pattern to §§ 5.4–5.5, pointed at `table-ready-production` / the production ALB DNS instead. Worth resisting the temptation to "simplify" by only running the migration step for staging and assuming production's schema is already caught up from some earlier deploy — decision #7 is explicit that production gets its own migration action on every promotion, specifically because the promotion isn't rebuilding anything, so this is the *only* place in the production path where a schema change actually gets applied.

### 5.8 IAM service roles

Two roles, both created in `infra/pipeline.yaml`:

**CodeBuild service role** (trust: `codebuild.amazonaws.com`), attached to *all* the CodeBuild projects above (or split per-project if you want tighter scoping — reasonable given Test/Build vs Deploy projects need quite different permissions):
- `ecr:GetAuthorizationToken` (account-wide, ECR requires this), plus `ecr:BatchCheckLayerAvailability`, `ecr:InitiateLayerUpload`, `ecr:UploadLayerPart`, `ecr:CompleteLayerUpload`, `ecr:PutImage`, `ecr:BatchGetImage` scoped to the `table-ready` repo ARN — needed by the Build project.
- `ecs:RunTask` scoped to the specific task definition ARNs (staging and production families), `ecs:DescribeTasks`, `ecs:UpdateService` and `ecs:DescribeServices` scoped to the two cluster/service ARNs, `ecs:RegisterTaskDefinition` (this action can't be resource-scoped by ARN — it's account-wide by design in IAM, since the resource doesn't exist yet at call time) — needed by the Deploy projects.
- `iam:PassRole` scoped to *exactly* the task execution role and task role ARNs from Phase 4 (not `*`) — required because registering/running a task definition means CodeBuild is handing those roles to ECS on your behalf; IAM requires the caller to explicitly be allowed to pass each role.
- `cloudformation:UpdateStack`, `cloudformation:DescribeStacks` scoped to the two app stack ARNs, if you go with the "update `ImageTag` via CloudFormation" approach from § 5.4.
- `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents` — CodeBuild's own build logs.

**CodePipeline service role** (trust: `codepipeline.amazonaws.com`):
- `codestar-connections:UseConnection` scoped to the connection ARN from Prerequisites §2.
- `codebuild:StartBuild`, `codebuild:BatchGetBuilds` scoped to each CodeBuild project ARn above.
- `s3:GetObject`, `s3:PutObject`, `s3:GetBucketVersioning` scoped to the artifact bucket (next paragraph).
- `sns:Publish` scoped to the approval topic ARN.

**S3 artifact bucket:** `AWS::S3::Bucket` with versioning enabled (CodePipeline requires it), no public access, in `infra/pipeline.yaml`. CodePipeline manages object lifecycle inside it automatically; a bucket lifecycle rule expiring old artifact versions after 30–90 days is a reasonable cost-hygiene addition, not required for correctness.

---

## Phase 6: Wrap-up & Documentation

`docs/testing.md`, `docs/deployment.md`, and `docs/release-process.md` get written **after** Phases 4 and 5 are real and working, describing what was actually built — not from this plan. What belongs here instead is the part of `release-process.md` that's genuinely a planning decision rather than a description of finished infrastructure: the rollback procedure. Work this out now, because it's much easier to think through calmly here than to invent it during an actual incident.

### The core idea: rollback is a forward deploy, not an undo

CodePipeline, CodeBuild, and `ecs update-service` all only know how to move forward. There is no "undo the last deploy" button. **"Rolling back" means: identify the last known-good image, and run it through the exact same Deploy-Production mechanism (§ 5.7) as any normal release** — `ecs:RunTask` for migration, then `update-service` — just supplying an older `ImageTag` parameter value instead of the newest one.

### Identifying the last known-good image

Because Phase 4's ECR repo has `IMMUTABLE` tags keyed by git commit SHA (§ 4.2), "last known-good" is just "the commit SHA that was deployed before the one you're rolling back from":

```bash
# What's running in production right now:
aws ecs describe-services --cluster table-ready-production --services table-ready-production \
  --query 'services[0].taskDefinition' --output text
# then inspect that task definition's container image to get the current tag/digest

aws ecs describe-task-definition --task-definition <arn-from-above> \
  --query 'taskDefinition.containerDefinitions[0].image'

# The full deploy history, oldest-to-newest, if you need to go back further
# than "one release ago":
aws ecr describe-images --repository-name table-ready \
  --query 'sort_by(imageDetails,&imagePushedAt)[].{tag:imageTags[0],pushedAt:imagePushedAt,digest:imageDigest}'
```

Cross-reference against git history (`git log --oneline`) to confirm the SHA you're about to redeploy is actually the commit you think it is — the ECR push timestamp tells you *when* an image was built, not necessarily *which* deploy was last known-good from a product/incident standpoint; that judgment call is yours, ECR just gives you the data to make it.

### Redeploying the old image

Same mechanism as § 5.4/5.7, run manually (this is an incident-response action, not something to wait for a `git push` and a full pipeline run to accomplish — speed matters here):

```bash
OLD_TAG=<the git sha you identified above>

aws ecs run-task \
  --cluster table-ready-production \
  --task-definition table-ready-production \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[...],securityGroups=[...],assignPublicIp=ENABLED}" \
  --overrides "{\"containerOverrides\":[{\"name\":\"app\",\"image\":\"<ecr-repo-uri>:$OLD_TAG\",\"command\":[\"uv\",\"run\",\"--no-sync\",\"alembic\",\"upgrade\",\"head\"]}]}"
# wait + check exit code exactly as in § 4.4/5.4

aws cloudformation deploy \
  --template-file infra/app-stack.yaml \
  --stack-name table-ready-production \
  --parameter-overrides EnvironmentName=production ImageTag=$OLD_TAG DesiredCount=1 MaxCount=2 \
  --capabilities CAPABILITY_NAMED_IAM
# then the usual update-service / wait services-stable
```

This is worth running against staging first if there's any time pressure allows for it at all, for the same reason any other deploy is worth staging first — but acknowledge in `release-process.md`, when it's written, that a genuine production incident may justify skipping straight to production.

### The harder case: rollback that also needs a migration reverted

Redeploying an old image is safe on its own only if the database schema the old code expects is still compatible with whatever's currently in the database. If the release being rolled back *added* a migration (a new column, table, etc.) that the old code doesn't know about, redeploying the old image alone can leave you with an old app talking to a newer schema — sometimes harmless (an unused new nullable column), sometimes not (a new `NOT NULL` column the old INSERT statements don't populate).

When that's the case, the migration needs reverting too, via `alembic downgrade`, as its own explicit step before redeploying the old image:

```bash
aws ecs run-task \
  --cluster table-ready-production \
  --task-definition table-ready-production \
  --launch-type FARGATE \
  --network-configuration "..." \
  --overrides '{"containerOverrides":[{"name":"app","command":["uv","run","--no-sync","alembic","downgrade","<target-revision>"]}]}'
```

`<target-revision>` is the revision ID the *old* code's migrations file expects as head — find it with `git show <old-sha>:backend/alembic/versions/` or `alembic history` checked out at that commit.

Two things worth flagging explicitly in `release-process.md` once this is written for real:

1. **This only works if `downgrade()` is actually implemented and correct** for every migration involved. As of this plan, the repo has exactly one migration (`b38117986837_initial_schema.py`, `down_revision: None`) and its `downgrade()` is implemented — but downgrading *that specific one* means dropping the entire schema, which is destructive in a way that's only acceptable pre-launch. As more migrations accumulate, this remains only as safe as each individual migration's `downgrade()` being written and tested, which is a discipline to establish going forward (test `upgrade` → `downgrade` → `upgrade` locally as part of writing any new migration), not something this plan can guarantee retroactively.
2. **Order matters and is easy to get backwards under pressure:** downgrade the schema *before* redeploying the old image that expects the older schema — not after. Redeploying the old image first against a not-yet-downgraded (newer) schema risks the exact same old-app-vs-new-schema mismatch this whole procedure exists to avoid, just transiently.
