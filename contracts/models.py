from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator


OFFER_STATUS = [
    ("pending", "Pending"),
    ("accepted", "Accepted"),
    ("rejected", "Rejected"),
    ("withdrawn", "Withdrawn"),
]


class JobOffer(models.Model):
    """An employer's formal offer to a candidate who applied to their job.

    Jobs are LONG-TERM recurring engagements. The offer carries the agreement
    terms (monthly rate, payment day, cadence, meeting terms). The freelancer
    signs the agreement (recorded in `agreement_signed_at`) before accepting;
    on accept a recurring Contract is created. `amount` is the monthly/period
    rate. There is at most one live (pending/accepted) offer per application.
    """

    job = models.ForeignKey(
        "ManageJobsTasks.Job", on_delete=models.CASCADE, related_name="job_offers"
    )
    application = models.ForeignKey(
        "ManageJobsTasks.JobApplication", on_delete=models.CASCADE, related_name="offers"
    )
    employer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="job_offers_sent"
    )
    freelancer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="job_offers_received"
    )

    # `amount` is the monthly rate for the recurring engagement.
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    note = models.TextField(blank=True, help_text="Optional scope note / message to the freelancer")

    # --- Recurring agreement terms ---
    payment_day = models.PositiveSmallIntegerField(
        default=1, help_text="Day of the month the payment is due (1-28)"
    )
    cadence = models.CharField(max_length=20, default="monthly")
    meeting_terms = models.TextField(blank=True, help_text="Availability / meeting terms in the agreement")
    # Set when the freelancer signs the agreement (at accept time).
    agreement_signed_at = models.DateTimeField(null=True, blank=True)

    # Legacy one-shot field, kept nullable for historical rows; unused for the
    # recurring model.
    delivery_days = models.PositiveIntegerField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=OFFER_STATUS, default="pending")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Offer on '{self.job.title}' to {self.freelancer.email} ({self.status})"


class TaskOffer(models.Model):
    """An employer's formal offer to a bidder on their task. The task-side twin
    of JobOffer: sourced from a TaskBidding instead of a JobApplication. When the
    freelancer accepts, a Contract is created (task-origin)."""

    task = models.ForeignKey(
        "ManageJobsTasks.Task", on_delete=models.CASCADE, related_name="task_offers"
    )
    bidding = models.ForeignKey(
        "ManageJobsTasks.TaskBidding", on_delete=models.CASCADE, related_name="offers"
    )
    employer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="task_offers_sent"
    )
    freelancer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="task_offers_received"
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    delivery_days = models.PositiveIntegerField(help_text="Agreed delivery time in days")
    note = models.TextField(blank=True, help_text="Optional scope note / message to the freelancer")

    status = models.CharField(max_length=20, choices=OFFER_STATUS, default="pending")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Task offer on '{self.task.project_name}' to {self.freelancer.email} ({self.status})"


CONTRACT_STATUS = [
    # One-shot (Task) lifecycle
    ("awaiting_funding", "Awaiting Funding"),
    ("funded", "Funded"),
    ("submitted", "Submitted"),
    ("in_review", "In Review"),
    ("revision_requested", "Revision Requested"),
    ("completed", "Completed"),
    ("disputed", "Disputed"),
    ("cancelled", "Cancelled"),
    # Recurring (Job) lifecycle
    ("active", "Active"),
    ("grace", "Grace Period"),
    ("pending_termination", "Pending Termination"),
    ("terminated", "Terminated"),
    ("ended", "Ended"),
]


class Contract(models.Model):
    """The working agreement created when a freelancer accepts an offer.

    Holds the agreed terms and drives the escrow + delivery lifecycle. A
    payments.Payment is attached to it (created NOT_INITIATED and funded via
    African Money). `deadline` is set from `delivery_days` when escrow funds.
    """

    # A contract originates from EITHER a Job (application + JobOffer) OR a Task
    # (bidding + TaskOffer). Exactly one side is populated; the rest are null.
    job = models.ForeignKey(
        "ManageJobsTasks.Job", on_delete=models.CASCADE, related_name="contracts",
        null=True, blank=True,
    )
    application = models.OneToOneField(
        "ManageJobsTasks.JobApplication", on_delete=models.CASCADE, related_name="contract",
        null=True, blank=True,
    )
    offer = models.OneToOneField(
        JobOffer, on_delete=models.CASCADE, related_name="contract", null=True, blank=True,
    )

    task = models.ForeignKey(
        "ManageJobsTasks.Task", on_delete=models.CASCADE, related_name="contracts",
        null=True, blank=True,
    )
    task_bidding = models.OneToOneField(
        "ManageJobsTasks.TaskBidding", on_delete=models.CASCADE, related_name="contract",
        null=True, blank=True,
    )
    task_offer = models.OneToOneField(
        TaskOffer, on_delete=models.CASCADE, related_name="contract", null=True, blank=True,
    )

    employer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="contracts_as_employer"
    )
    freelancer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="contracts_as_freelancer"
    )

    # For a Task this is the one-shot amount; for a Job it is the monthly rate
    # (also copied to `monthly_rate` below for clarity).
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    # One-shot only (Task). Null for recurring Job contracts.
    delivery_days = models.PositiveIntegerField(null=True, blank=True)
    terms = models.TextField(blank=True)

    status = models.CharField(max_length=30, choices=CONTRACT_STATUS, default="awaiting_funding")
    deadline = models.DateTimeField(null=True, blank=True)
    # Latest note the employer left when requesting a change, shown to the
    # freelancer so they know what to fix before resubmitting.
    review_note = models.TextField(blank=True)

    # --- Recurring (Job) engagement config ---
    is_recurring = models.BooleanField(default=False)
    monthly_rate = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    payment_day = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Day of month payment is due")
    cadence = models.CharField(max_length=20, blank=True, default="")
    meeting_terms = models.TextField(blank=True)
    review_window_days = models.PositiveSmallIntegerField(default=4, help_text="Days at period end to review before auto-release")
    grace_period_days = models.PositiveSmallIntegerField(default=10, help_text="Days after a missed funding before termination opens")
    agreement_signed_at = models.DateTimeField(null=True, blank=True)
    # Set once when the grace period elapses and the freelancer is invited to
    # terminate (guards the one-time nudge email).
    termination_offered_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def subject_title(self):
        """The job title or task name this contract is for, whichever applies."""
        if self.job_id:
            return self.job.title
        if self.task_id:
            return self.task.project_name
        return "Contract"

    @property
    def source_type(self):
        return "task" if self.task_id else "job"

    def __str__(self):
        return f"Contract on '{self.subject_title}' ({self.status})"


BILLING_PERIOD_STATUS = [
    ("awaiting_funding", "Awaiting Funding"),
    ("funded", "Funded"),
    ("in_review", "In Review"),
    ("released", "Released"),
    ("disputed", "Disputed"),
    ("missed", "Missed"),
]


class BillingPeriod(models.Model):
    """One monthly cycle of a recurring (Job) contract. The employer pre-funds
    escrow for the period; at period end a review window opens, after which the
    escrow auto-releases to the freelancer. Managed by `process_billing_cycles`."""

    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name="periods")
    period_number = models.PositiveIntegerField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    funding_due_date = models.DateTimeField(help_text="Employer must fund escrow by this time")
    review_window_end = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=BILLING_PERIOD_STATUS, default="awaiting_funding")
    reminder_sent = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["contract", "period_number"]
        constraints = [
            models.UniqueConstraint(fields=["contract", "period_number"], name="unique_period_per_contract"),
        ]

    def __str__(self):
        return f"Period {self.period_number} of contract {self.contract_id} ({self.status})"


class ContractDocument(models.Model):
    """A file attached to a contract (employer requirements, references, etc.).
    Either party may upload; both parties can view and download."""

    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name="documents")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="contract_documents")
    file = models.FileField(upload_to="contracts/documents/")
    label = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"Document for contract {self.contract_id}: {self.label or self.file.name}"


class ProjectSubmission(models.Model):
    """A freelancer's delivery of the work on a contract. Supports resubmission:
    each new submission bumps `version`, so a revision after a change request is
    a new submission rather than an edit of the old one."""

    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name="submissions")
    # For recurring (Job) contracts a submission belongs to a specific Assignment;
    # null for one-shot (Task) contract-level submissions.
    assignment = models.ForeignKey(
        "Assignment", on_delete=models.CASCADE, related_name="submissions", null=True, blank=True
    )
    message = models.TextField(blank=True, help_text="Notes to the client about this delivery")
    version = models.PositiveIntegerField(default=1)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"Submission v{self.version} for contract {self.contract_id}"


class SubmissionFile(models.Model):
    submission = models.ForeignKey(ProjectSubmission, on_delete=models.CASCADE, related_name="files")
    file = models.FileField(upload_to="contracts/submissions/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"File for submission {self.submission_id}"


DISPUTE_STATUS = [
    ("open", "Open"),
    ("under_review", "Under Review"),
    ("resolved_released", "Resolved - Released to Freelancer"),
    ("resolved_refunded", "Resolved - Refunded to Employer"),
    ("rejected", "Rejected"),
]


class Dispute(models.Model):
    """A disagreement on a contract (employer rejects the work, or freelancer
    contests a revision request). Resolved manually by an admin."""

    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name="disputes")
    raised_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="disputes_raised")
    reason = models.TextField()
    status = models.CharField(max_length=30, choices=DISPUTE_STATUS, default="open")
    admin_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Dispute on contract {self.contract_id} ({self.status})"


ASSIGNMENT_STATUS = [
    ("open", "Open"),
    ("submitted", "Submitted"),
    ("changes_requested", "Changes Requested"),
    ("accepted", "Accepted"),
]


class Assignment(models.Model):
    """A unit of work the employer hands the freelancer on a recurring (Job)
    contract. Freelancer submits deliverables (ProjectSubmission) against it and
    the employer accepts or requests changes. Payment stays period-based;
    assignments are work-tracking within a period."""

    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name="assignments")
    period = models.ForeignKey(
        BillingPeriod, on_delete=models.SET_NULL, null=True, blank=True, related_name="assignments"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=ASSIGNMENT_STATUS, default="open")
    review_note = models.TextField(blank=True, help_text="Employer's note when requesting changes")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assignments_created")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Assignment '{self.title}' on contract {self.contract_id} ({self.status})"


class AssignmentFile(models.Model):
    """A brief/reference file the employer attaches to an assignment."""

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="files")
    file = models.FileField(upload_to="contracts/assignments/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"File for assignment {self.assignment_id}"


TERMINATION_STATUS = [
    ("pending", "Pending"),
    ("approved", "Approved (Terminated)"),
    ("denied", "Denied"),
]


class TerminationRequest(models.Model):
    """A request (by either party) to end a recurring contract. Never ends the
    contract directly: an admin verifies and executes. On approval, funded work
    is settled to the freelancer and the contract is terminated."""

    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name="termination_requests")
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="termination_requests")
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=TERMINATION_STATUS, default="pending")
    admin_note = models.TextField(blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="termination_reviews"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Termination request on contract {self.contract_id} ({self.status})"
