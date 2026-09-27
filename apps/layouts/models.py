from django.db import models

from apps.stores.models import Store


class LayoutStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    READY = "ready", "Ready"
    ARCHIVED = "archived", "Archived"


class SourceFormat(models.TextChoices):
    DWG = "dwg", "DWG"
    DXF = "dxf", "DXF"
    RVT = "rvt", "RVT"
    IFC = "ifc", "IFC"


class StoreLayout(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="layouts")
    name = models.CharField(max_length=200, default="Active layout")
    is_active = models.BooleanField(default=True)
    source_format = models.CharField(
        max_length=8, choices=SourceFormat.choices, blank=True, default=""
    )
    source_filename = models.CharField(max_length=255, blank=True, default="")
    units = models.CharField(max_length=16, default="mm")
    scale_factor = models.FloatField(default=1.0)
    origin_offset_x_mm = models.IntegerField(default=0)
    origin_offset_y_mm = models.IntegerField(default=0)
    rotation_deg = models.FloatField(default=0.0)
    status = models.CharField(
        max_length=16, choices=LayoutStatus.choices, default=LayoutStatus.DRAFT
    )
    confidence_pct = models.PositiveSmallIntegerField(null=True, blank=True)
    needs_review_counts = models.JSONField(default=dict, blank=True)
    overlays = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_active", "-updated_at"]

    def __str__(self) -> str:
        return f"{self.store.name} layout ({'active' if self.is_active else 'inactive'})"


class IngestJob(models.Model):
    class State(models.TextChoices):
        QUEUED = "queued", "Queued"
        PROCESSING = "processing", "Processing"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"

    layout = models.ForeignKey(
        StoreLayout, on_delete=models.CASCADE, related_name="ingest_jobs"
    )
    state = models.CharField(max_length=16, choices=State.choices, default=State.QUEUED)
    progress = models.PositiveSmallIntegerField(default=0)
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
