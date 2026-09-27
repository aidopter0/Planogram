from django.conf import settings
from django.db import models


class Role(models.TextChoices):
    VIEWER = "viewer", "Viewer"
    DESIGNER = "designer", "Designer"
    PRODUCT_STEWARD = "product_steward", "Product Steward"
    CATALOG_ADMIN = "catalog_admin", "Catalog Admin"
    ADMIN = "admin", "Admin"


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    role = models.CharField(max_length=32, choices=Role.choices, default=Role.DESIGNER)
    must_change_password = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.user.username} ({self.role})"


class OrgSettings(models.Model):
    """Singleton org settings for the deployment."""

    name = models.CharField(max_length=200, default="Planogram Org")
    default_bay_width_mm = models.PositiveIntegerField(default=900)
    display_units = models.CharField(max_length=8, default="mm")
    zip_match_pattern = models.CharField(max_length=64, default="{sku}")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Org settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls) -> "OrgSettings":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self) -> str:
        return self.name
