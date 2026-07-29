from django.contrib import admin, messages

from .models import Payment, Wallet, Transaction, BankAccount, Escrow, Withdrawal
from .services.withdrawal_service import WithdrawalService, WithdrawalError


@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    """Admin queue for manual payouts. Verify the bank details, then use the
    'Mark as paid' action (debits the wallet + writes a DEBIT transaction) or
    'Reject'."""

    list_display = (
        "id", "user", "amount", "status", "bank_name", "account_name",
        "account_number", "created_at", "processed_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("user__email", "account_number", "account_name", "bank_name")
    readonly_fields = ("created_at", "processed_at")
    actions = ["mark_paid", "reject_withdrawals"]

    @admin.action(description="Mark as paid (debit wallet)")
    def mark_paid(self, request, queryset):
        done, failed = 0, 0
        for w in queryset:
            try:
                WithdrawalService.mark_paid(w)
                done += 1
            except WithdrawalError as e:
                failed += 1
                self.message_user(request, f"#{w.id}: {e}", level=messages.ERROR)
        if done:
            self.message_user(request, f"{done} withdrawal(s) marked paid and wallets debited.", level=messages.SUCCESS)
        if failed:
            self.message_user(request, f"{failed} could not be paid.", level=messages.WARNING)

    @admin.action(description="Reject selected withdrawals")
    def reject_withdrawals(self, request, queryset):
        count = 0
        for w in queryset:
            try:
                WithdrawalService.reject(w, note="Rejected by admin")
                count += 1
            except WithdrawalError as e:
                self.message_user(request, f"#{w.id}: {e}", level=messages.ERROR)
        if count:
            self.message_user(request, f"{count} withdrawal(s) rejected.", level=messages.SUCCESS)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "employer", "freelancer", "amount", "commission_amount", "vat_amount", "net_amount", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("employer__email", "freelancer__email", "payment_reference")


admin.site.register(Wallet)
admin.site.register(Transaction)
admin.site.register(BankAccount)
admin.site.register(Escrow)
