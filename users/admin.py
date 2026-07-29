from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import UserProfile, Category, Appeal


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(UserProfile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "tagline", "category", "nationality", "hourly_rate", "job_success", "rating", "verified")
    list_filter = ("category", "nationality", "verified")
    search_fields = ("user__email", "user__first_name", "user__last_name", "tagline")


@admin.register(Appeal)
class AppealAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "account_status", "status", "created_at", "reviewed_by", "reviewed_at")
    list_filter = ("status", "account_status")
    search_fields = ("user__email", "message")
    readonly_fields = ("user", "account_status", "message", "created_at")