from django.db import models


class Orientation(models.TextChoices):
    NORMAL = "normal", "Normal"
    ROTATED_90 = "rotated_90", "Rotated 90°"


class Readiness(models.TextChoices):
    IMPORT_VALID = "import_valid", "Import-valid"
    ARRANGE_READY = "arrange_ready", "Arrange-ready"
    IMAGE_COMPLETE = "image_complete", "Image-complete"


class Product(models.Model):
    """Org-global Product Master — no store_id."""

    sku = models.CharField(max_length=64, unique=True)
    barcode = models.CharField(max_length=64, blank=True, default="")
    name = models.CharField(max_length=255)
    brand = models.CharField(max_length=120, blank=True, default="")
    category = models.CharField(max_length=120, blank=True, default="")
    subcategory = models.CharField(max_length=120, blank=True, default="")
    width_mm = models.PositiveIntegerField()
    height_mm = models.PositiveIntegerField(default=0)
    depth_mm = models.PositiveIntegerField(default=0)
    orientation = models.CharField(
        max_length=16, choices=Orientation.choices, default=Orientation.NORMAL
    )
    front_image = models.ImageField(upload_to="products/", blank=True, null=True)
    pack_type = models.CharField(max_length=64, blank=True, default="")
    image_incomplete = models.BooleanField(default=True)
    readiness = models.CharField(
        max_length=32, choices=Readiness.choices, default=Readiness.IMPORT_VALID
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sku"]

    def __str__(self) -> str:
        return f"{self.sku} — {self.name}"

    def effective_width_mm(self, orientation: str | None = None) -> int:
        """A32: normal → width_mm; rotated_90 → height_mm."""
        orient = orientation or self.orientation
        if orient == Orientation.ROTATED_90:
            return int(self.height_mm or self.width_mm)
        return int(self.width_mm)


class ProductImportJob(models.Model):
    class State(models.TextChoices):
        QUEUED = "queued", "Queued"
        PROCESSING = "processing", "Processing"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"

    state = models.CharField(max_length=16, choices=State.choices, default=State.QUEUED)
    report = models.JSONField(default=dict, blank=True)
    created_count = models.PositiveIntegerField(default=0)
    updated_count = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
