Estimate: about 40–70 focused hours, or roughly 1–2 working weeks full-time. Part-time around the Zoomcamp, expect 3–5 weeks on the calendar. Someone who already knows CloudFormation and ECS could do it in 2–3 days. The upper end assumes this is your first time hand-writing a VPC, ECS service and CodePipeline in CloudFormation.

| Chunk | Hours | Notes |
| :--- | :--- | :--- |
| Prerequisites (IAM user, CodeStar connection, CLI profile) | 1–2 | Mostly clicking and waiting on the GitHub auth step |
| 4.1 `/api/health` endpoint + test | 1 | Small, and you can do it with no AWS at all |
| 4.2 ECR repo | 0.25 | One command |
| 4.3 `infra/app-stack.yaml` | 12–20 | The biggest chunk. About 25–30 resources, plus checking whether Express Mode has a CloudFormation resource type |
| 4.4 First deploy + migration, staging and prod | 4–8 | Mostly waiting on deploy loops and debugging |
| 5.1–5.3 Pipeline, Source/Test/Build stages | 10–16 | The Build stage is the riskiest part: Docker-in-Docker with Compose and Playwright inside CodeBuild |
| 5.4–5.7 Deploy, smoke test, approval, prod | 6–10 | See the design gap below |
| 5.8 IAM service roles | 3–6 | Fixing AccessDenied errors one at a time |
| Phase 6 rollback rehearsal in staging | 2–4 | Worth doing once for real, not just reading |

### Why the range is so wide

* Each CloudFormation attempt is slow. A stack with RDS takes 10–20 minutes to create. A failure can also take a while to roll back, because RDS gets deleted. Plan on 5–10 failed attempts on `app-stack.yaml`, so wall-clock time far exceeds typing time.
* The plan leaves three things for you to check. The ⚠️ items (the Express Mode resource type, `Fn::Sub` with a secret reference inside it, and `RunTask` under Express Mode) could each cost anywhere from 20 minutes to half a day.
* The Build stage needs trial and error. Getting Chromium and Postgres to run inside CodeBuild usually takes a few tries (privileged mode, memory size, Playwright system packages). Each try is a full pipeline run.

### A design gap in §5.4 that will cost time if you don't settle it first

The Deploy step runs the migration with `run-task --task-definition table-ready-staging`. That task definition still points at the old image, so the migration runs the previous release's Alembic files. §5.4 then suggests updating `ImageTag` through CloudFormation, but doesn't say when that happens relative to the migration. Pick one of these before building:

* Pass the new image as a container override on the migration `run-task`, the same way the Phase 6 rollback section already does.
* Or run `cloudformation deploy` with the new tag first, then migrate. The catch is that the new tasks start before the schema exists.

The first option is cleaner. With the CloudFormation route, the CodeBuild role also needs permission to update every resource in the stack, not just the few listed in §5.8. That will send you round the AccessDenied loop again.

### Ways to cut the time down

* Deploy the stack in layers: networking and security groups, then RDS, then ECS and the ALB. You fix errors in small pieces instead of waiting on the whole stack.
* Use `--disable-rollback` on create while debugging, so a failed stack stays up and you can inspect it.
* Do the pipeline in two passes. First get Source → Test → Build working with no deploy stages. Add Deploy, Smoke Test and Approval once images reliably reach ECR.
* Tear the stacks down between sessions. Each environment runs an ALB and an RDS instance, which cost money while idle.