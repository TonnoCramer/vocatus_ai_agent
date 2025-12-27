from django.conf import settings
from django.db import models


class AIRequestLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ai_requests",
    )
    session_key = models.CharField(max_length=40)
    timestamp = models.DateTimeField(auto_now_add=True)

    input_tokens = models.IntegerField()
    output_tokens = models.IntegerField()
    request_cost = models.DecimalField(max_digits=10, decimal_places=6)

    def __str__(self):
        return f"{self.user or 'anon'} - {self.timestamp} - €{self.request_cost}"
