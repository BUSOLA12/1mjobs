from django.contrib import admin, messages
from django.utils import timezone

from .models import JobOffer, TaskOffer, Contract, ContractDocument, ProjectSubmission, SubmissionFile, Dispute


@admin.register(JobOffer)
class JobOfferAdmin(admin.ModelAdmin):
    list_display = ("id", "job", "employer", "freelancer", "amount", "delivery_days", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("job__title", "employer__email", "freelancer__email")


@admin.register(TaskOffer)
class TaskOfferAdmin(admin.ModelAdmin):
    list_display = ("id", "task", "employer", "freelancer", "amount", "delivery_days", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("task__project_name", "employer__email", "freelancer__email")


class ContractDocumentInline(admin.TabularInline):
    model = ContractDocument
    extra = 0


class SubmissionFileInline(admin.TabularInline):
    model = SubmissionFile
    extra = 0


@admin.register(ProjectSubmission)
class ProjectSubmissionAdmin(admin.ModelAdmin):
    list_display = ("id", "contract", "version", "submitted_at")
    inlines = [SubmissionFileInline]


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ("id", "subject", "source_type", "employer", "freelancer", "amount", "delivery_days", "status", "deadline", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("job__title", "task__project_name", "employer__email", "freelancer__email")
    inlines = [ContractDocumentInline]

    @admin.display(description="Subject")
    def subject(self, obj):
        return obj.subject_title


@admin.register(Dispute)
class DisputeAdmin(admin.ModelAdmin):
    """Admin queue for disputes. 'Resolve - release' pays the freelancer from
    escrow and completes the contract. 'Resolve - refund' marks it refunded and
    cancels the contract (the actual money return to the employer is handled
    off-platform, since African Money refunds are manual)."""

    list_display = ("id", "contract", "raised_by", "status", "created_at", "resolved_at")
    list_filter = ("status", "created_at")
    search_fields = ("contract__job__title", "raised_by__email")
    readonly_fields = ("created_at", "resolved_at")
    actions = ["resolve_release", "resolve_refund", "mark_under_review"]

    @admin.action(description="Mark under review")
    def mark_under_review(self, request, queryset):
        queryset.filter(status="open").update(status="under_review")
        self.message_user(request, "Selected disputes marked under review.", level=messages.SUCCESS)

    @admin.action(description="Resolve - release escrow to freelancer")
    def resolve_release(self, request, queryset):
        from payments.services.payment_service import PaymentService
        done = 0
        for d in queryset.exclude(status__in=["resolved_released", "resolved_refunded"]):
            contract = d.contract
            payment = contract.payments.filter(status="ESCROWED").order_by("-created_at").first()
            if not payment:
                self.message_user(request, f"Dispute #{d.id}: no escrowed payment.", level=messages.ERROR)
                continue
            PaymentService.release_payment(payment)
            contract.status = "completed"
            contract.save(update_fields=["status", "updated_at"])
            d.status = "resolved_released"
            d.resolved_at = timezone.now()
            d.save(update_fields=["status", "resolved_at"])
            done += 1
        if done:
            self.message_user(request, f"{done} dispute(s) resolved and released.", level=messages.SUCCESS)

    @admin.action(description="Resolve - refund employer (money handled off-platform)")
    def resolve_refund(self, request, queryset):
        for d in queryset.exclude(status__in=["resolved_released", "resolved_refunded"]):
            contract = d.contract
            contract.status = "cancelled"
            contract.save(update_fields=["status", "updated_at"])
            d.status = "resolved_refunded"
            d.resolved_at = timezone.now()
            d.save(update_fields=["status", "resolved_at"])
        self.message_user(request, "Selected disputes marked refunded and contracts cancelled.", level=messages.SUCCESS)
