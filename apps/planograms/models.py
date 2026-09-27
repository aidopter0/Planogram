from django.conf import settings
from django.db import models

from apps.stores.models import Store


class PlanogramStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    READY_FOR_REVIEW = "ready_for_review", "Ready for review"
    ARCHIVED = "archived", "Archived"


class Planogram(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="planograms")
    name = models.CharField(max_length=200)
    status = models.CharField(
        max_length=32, choices=PlanogramStatus.choices, default=PlanogramStatus.DRAFT
    )
    tags = models.JSONField(default=list, blank=True)
    # Target fixture set: list of fixture instance IDs (bay scope for Must).
    target_fixture_ids = models.JSONField(default=list, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_planograms",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"{self.store.name} / {self.name}"


class PlanogramScene(models.Model):
    """JSONB scene graph: placements + Product Blocks (A20)."""

    planogram = models.OneToOneField(
        Planogram, on_delete=models.CASCADE, related_name="scene"
    )
    schema_version = models.PositiveIntegerField(default=5)
    graph = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Scene for {self.planogram_id}"
