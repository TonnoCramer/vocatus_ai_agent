from django.contrib import admin
from .models import AIRequestLog


@admin.register(AIRequestLog)
class AIRequestLogAdmin(admin.ModelAdmin):
    list_display = (
        "timestamp",
        "user",
        "session_key",
        "request_cost",
    )
    list_filter = ("user", "timestamp")
    ordering = ("-timestamp",)
    search_fields = ("user__username", "session_key")