from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import UserProfile, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(UserProfile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "tagline", "category", "nationality", "hourly_rate", "job_success", "rating", "verified")
    list_filter = ("category", "nationality", "verified")
    search_fields = ("user__email", "user__first_name", "user__last_name", "tagline")