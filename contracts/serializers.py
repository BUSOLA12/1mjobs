from rest_framework import serializers

from .models import (
    JobOffer, TaskOffer, Contract, ContractDocument, ProjectSubmission, SubmissionFile,
    Dispute, BillingPeriod, Assignment, AssignmentFile, TerminationRequest,
)


class JobOfferSerializer(serializers.ModelSerializer):
    """Read serializer for an offer. Exposes light job/applicant context so the
    dashboards can render offers without extra round-trips. The freelancer's
    email is never included (only names)."""

    job_title = serializers.SerializerMethodField(read_only=True)
    employer_name = serializers.SerializerMethodField(read_only=True)
    freelancer_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = JobOffer
        fields = (
            "id", "job", "job_title", "application", "amount",
            "payment_day", "cadence", "meeting_terms", "agreement_signed_at",
            "note", "status", "created_at", "updated_at",
            "employer", "employer_name", "freelancer", "freelancer_name",
        )
        read_only_fields = fields

    def get_job_title(self, obj):
        return obj.job.title if obj.job_id else None

    def get_employer_name(self, obj):
        return obj.employer.get_full_name or obj.employer.email

    def get_freelancer_name(self, obj):
        return obj.freelancer.get_full_name or obj.freelancer.email


class JobOfferCreateSerializer(serializers.Serializer):
    """Employer's Send Offer payload for a recurring Job engagement. Tied to an
    application; job/employer/freelancer are derived server-side. `amount` is the
    monthly rate."""

    application = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    payment_day = serializers.IntegerField(min_value=1, max_value=28)
    cadence = serializers.CharField(required=False, allow_blank=True, default="monthly")
    meeting_terms = serializers.CharField(required=False, allow_blank=True, default="")
    note = serializers.CharField(required=False, allow_blank=True, default="")


class TaskOfferSerializer(serializers.ModelSerializer):
    """Read serializer for a task offer. Task-side twin of JobOfferSerializer.
    The freelancer's email is never included (only names)."""

    task_title = serializers.SerializerMethodField(read_only=True)
    employer_name = serializers.SerializerMethodField(read_only=True)
    freelancer_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = TaskOffer
        fields = (
            "id", "task", "task_title", "bidding", "amount", "delivery_days",
            "note", "status", "created_at", "updated_at",
            "employer", "employer_name", "freelancer", "freelancer_name",
        )
        read_only_fields = fields

    def get_task_title(self, obj):
        return obj.task.project_name if obj.task_id else None

    def get_employer_name(self, obj):
        return obj.employer.get_full_name or obj.employer.email

    def get_freelancer_name(self, obj):
        return obj.freelancer.get_full_name or obj.freelancer.email


class TaskOfferCreateSerializer(serializers.Serializer):
    """Validates the employer's Send Offer payload for a task. Tied to a bidding;
    task/employer/freelancer are derived server-side in the view."""

    bidding = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    delivery_days = serializers.IntegerField(min_value=1, max_value=365)
    note = serializers.CharField(required=False, allow_blank=True, default="")


class ContractDocumentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField(read_only=True)
    uploaded_by_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ContractDocument
        fields = ("id", "label", "file_url", "uploaded_by", "uploaded_by_name", "uploaded_at")
        read_only_fields = fields

    def get_file_url(self, obj):
        request = self.context.get("request")
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url if obj.file else None

    def get_uploaded_by_name(self, obj):
        return obj.uploaded_by.get_full_name or obj.uploaded_by.email


class SubmissionFileSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = SubmissionFile
        fields = ("id", "file_url", "uploaded_at")
        read_only_fields = fields

    def get_file_url(self, obj):
        request = self.context.get("request")
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url if obj.file else None


class ProjectSubmissionSerializer(serializers.ModelSerializer):
    files = SubmissionFileSerializer(many=True, read_only=True)

    class Meta:
        model = ProjectSubmission
        fields = ("id", "assignment", "message", "version", "submitted_at", "files")
        read_only_fields = fields


class AssignmentFileSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = AssignmentFile
        fields = ("id", "file_url", "uploaded_at")
        read_only_fields = fields

    def get_file_url(self, obj):
        request = self.context.get("request")
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url if obj.file else None


class AssignmentSerializer(serializers.ModelSerializer):
    files = AssignmentFileSerializer(many=True, read_only=True)
    submissions = ProjectSubmissionSerializer(many=True, read_only=True)
    created_by_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Assignment
        fields = (
            "id", "period", "title", "description", "status", "review_note",
            "created_by", "created_by_name", "created_at", "updated_at",
            "files", "submissions",
        )
        read_only_fields = fields

    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name or obj.created_by.email


class DisputeSerializer(serializers.ModelSerializer):
    raised_by_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Dispute
        fields = ("id", "reason", "status", "admin_note", "raised_by", "raised_by_name", "created_at", "resolved_at")
        read_only_fields = fields

    def get_raised_by_name(self, obj):
        return obj.raised_by.get_full_name or obj.raised_by.email


class BillingPeriodSerializer(serializers.ModelSerializer):
    payment = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = BillingPeriod
        fields = (
            "id", "period_number", "start_date", "end_date", "amount",
            "funding_due_date", "review_window_end", "status", "payment",
        )
        read_only_fields = fields

    def get_payment(self, obj):
        p = obj.payments.exclude(status="RELEASED").order_by("-created_at").first() \
            or obj.payments.order_by("-created_at").first()
        if not p:
            return None
        return {"id": p.id, "status": p.status, "payment_url": p.payment_url}


class TerminationRequestSerializer(serializers.ModelSerializer):
    requested_by_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = TerminationRequest
        fields = (
            "id", "reason", "status", "admin_note", "requested_by", "requested_by_name",
            "created_at", "resolved_at",
        )
        read_only_fields = fields

    def get_requested_by_name(self, obj):
        return obj.requested_by.get_full_name or obj.requested_by.email


class ContractSerializer(serializers.ModelSerializer):
    """Contract for either party's dashboard. Includes light job/party context,
    the escrow payment state (so the UI can show Fund Escrow / Funded), the
    attached documents, work submissions, and disputes. No emails are exposed."""

    # `job_title` keeps its name for the frontend but resolves to the job title
    # or the task name, whichever the contract originated from.
    job_title = serializers.SerializerMethodField(read_only=True)
    source_type = serializers.CharField(read_only=True)
    employer_name = serializers.SerializerMethodField(read_only=True)
    freelancer_name = serializers.SerializerMethodField(read_only=True)
    documents = ContractDocumentSerializer(many=True, read_only=True)
    submissions = ProjectSubmissionSerializer(many=True, read_only=True)
    disputes = DisputeSerializer(many=True, read_only=True)
    periods = BillingPeriodSerializer(many=True, read_only=True)
    assignments = AssignmentSerializer(many=True, read_only=True)
    termination_requests = TerminationRequestSerializer(many=True, read_only=True)
    payment = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Contract
        fields = (
            "id", "job", "task", "source_type", "job_title", "amount", "delivery_days", "terms",
            "status", "deadline", "review_note", "created_at", "updated_at",
            "is_recurring", "monthly_rate", "payment_day", "cadence", "meeting_terms",
            "review_window_days", "grace_period_days", "agreement_signed_at", "termination_offered_at",
            "employer", "employer_name", "freelancer", "freelancer_name",
            "documents", "submissions", "disputes", "periods", "assignments",
            "termination_requests", "payment",
        )
        read_only_fields = fields

    def get_job_title(self, obj):
        return obj.subject_title

    def get_employer_name(self, obj):
        return obj.employer.get_full_name or obj.employer.email

    def get_freelancer_name(self, obj):
        return obj.freelancer.get_full_name or obj.freelancer.email

    def get_payment(self, obj):
        # The active escrow payment (the one that is not RELEASED, if any).
        payment = obj.payments.exclude(status="RELEASED").order_by("-created_at").first()
        if not payment:
            payment = obj.payments.order_by("-created_at").first()
        if not payment:
            return None
        return {
            "id": payment.id,
            "status": payment.status,
            "payment_url": payment.payment_url,
        }
