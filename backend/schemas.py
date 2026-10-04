"""Request bodies and composite/derived response shapes (not persisted entities)."""

from typing import Literal

from pydantic import BaseModel, Field

from backend.models import (
    EntryMode,
    LargePartyEnquiry,
    Notification,
    NotificationChannel,
    NotificationRecipientType,
    NotificationTemplateType,
    Table,
    Venue,
    WaitlistEntry,
    WaitlistStatus,
)


class Error(BaseModel):
    code: str
    message: str


class LoginRequest(BaseModel):
    username: str
    password: str


class CreateGuestEntryRequest(BaseModel):
    guestName: str
    partySize: int
    mobileNumber: str
    seatingNote: str | None = None
    policyAcknowledged: bool


class CreateGuestEntryResultEntry(BaseModel):
    kind: Literal["entry"] = "entry"
    entry: WaitlistEntry
    accessToken: str
    message: str


class CreateGuestEntryResultLargePartyEnquiry(BaseModel):
    kind: Literal["large_party_enquiry"] = "large_party_enquiry"
    enquiry: LargePartyEnquiry
    message: str


class CreateGuestEntryResultClosed(BaseModel):
    kind: Literal["closed"] = "closed"
    message: str


CreateGuestEntryResult = (
    CreateGuestEntryResultEntry
    | CreateGuestEntryResultLargePartyEnquiry
    | CreateGuestEntryResultClosed
)


class GuestStatus(BaseModel):
    ticketCode: str
    guestName: str
    partySize: int
    status: WaitlistStatus
    estimatedWaitMinutes: int
    message: str
    notifiedAt: str | None = None
    returnByAt: str | None = None
    needsAttention: bool
    cancellationAllowed: bool
    venueName: str
    venueLogoPlaceholderLabel: str
    serviceDate: str


class SeatEntryRequest(BaseModel):
    tableId: str
    seatingOverrideReason: str | None = None


class ExtendReturnByRequest(BaseModel):
    additionalMinutes: int


class UpdateWaitEstimateRequest(BaseModel):
    estimatedWaitMinutes: int = Field(ge=0)


class PartialDefaultWaitEstimateMinutes(BaseModel):
    A: int | None = None
    B: int | None = None
    C: int | None = None
    D: int | None = None


class PartialVenueMessageSettings(BaseModel):
    joinMessage: str | None = None
    policyAcknowledgementMessage: str | None = None
    confirmationMessage: str | None = None
    tableReadyMessage: str | None = None
    cancellationMessage: str | None = None
    closedWaitlistMessage: str | None = None
    largePartyMessage: str | None = None
    largePartyConfirmationMessage: str | None = None


class UpdateVenueRequest(BaseModel):
    name: str | None = None
    contactPhone: str | None = None
    staffNotificationEmail: str | None = None
    menuUrl: str | None = None
    maxOnlinePartySize: int | None = None
    gracePeriodMinutes: int | None = None
    entryMode: EntryMode | None = None
    waitlistOpen: bool | None = None
    defaultWaitEstimateMinutes: PartialDefaultWaitEstimateMinutes | None = None
    messages: PartialVenueMessageSettings | None = None


class NotificationResult(BaseModel):
    entry: WaitlistEntry
    notification: Notification


class LargePartyEnquiryRequest(BaseModel):
    guestName: str
    partySize: int
    mobileNumber: str
    note: str | None = None


class DashboardSummary(BaseModel):
    activeWaiting: int
    pendingReview: int
    notified: int
    needsAttention: int


class DashboardData(BaseModel):
    venue: Venue
    serviceDate: str
    summary: DashboardSummary
    entries: list[WaitlistEntry]
    tables: list[Table]


class CreateTableRequest(BaseModel):
    name: str
    minCapacity: int = Field(ge=1)
    maxCapacity: int = Field(ge=1)
    notes: str | None = None


class UpdateTableRequest(BaseModel):
    name: str | None = None
    minCapacity: int | None = Field(default=None, ge=1)
    maxCapacity: int | None = Field(default=None, ge=1)
    active: bool | None = None
    notes: str | None = None


class SetTableAvailabilityRequest(BaseModel):
    availabilityState: Literal["available", "needs_tidying"]


class CreateNotificationEventRequest(BaseModel):
    entryId: str | None = None
    recipientType: NotificationRecipientType
    channel: NotificationChannel
    templateType: NotificationTemplateType
    renderedMessage: str
