
from django.db import models
from django.conf import settings

class MedicalReport(models.Model):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    report_type = models.CharField(max_length=50)

    report_file = models.FileField(
        upload_to='medical_reports/'
    )

    extracted_text = models.TextField(
        blank=True,
        null=True
    )

    analysis_result = models.JSONField(
        blank=True,
        null=True
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)