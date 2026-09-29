from django.db import models


class PlacementMode(models.TextChoices):
    ATTACHED = "ATTACHED", "Attached"
    FLOOR = "FLOOR", "Floor"
    WALL = "WALL", "Wall"
    CEILING = "CEILING", "Ceiling"
    FIXTURE_FACE = "FIXTURE_FACE", "Fixture face"
    SHELF = "SHELF", "Shelf"
    PEGBOARD = "PEGBOARD", "Pegboard"


class FixtureType(models.Model):
    """Org-global fixture type catalog — no store_id."""

    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=200)
    family = models.CharField(max_length=64, default="gondola")
    tier = models.PositiveSmallIntegerField(default=1)
    default_params = models.JSONField(default=dict, blank=True)
    param_schema = models.JSONField(default=dict, blank=True)
    placement_mode_options = models.JSONField(default=list, blank=True)
    thumbnail = models.ImageField(upload_to="catalog/fixtures/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["family", "name"]

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"


class FixtureComponentType(models.Model):
    """Org-global component type (shelf, pegboard, divider, …)."""

    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=200)
    family = models.CharField(max_length=64, default="shelf")
    default_params = models.JSONField(default=dict, blank=True)
    placement_mode_options = models.JSONField(default=list, blank=True)
    # Width-consuming insets reserved on carrier (D3).
    reserved_inset_mm = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["family", "name"]

    def __str__(self) -> str:
        return self.name


class DisplayAssetType(models.Model):
    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=200)
    family = models.CharField(max_length=64, default="endcap")
    placement_mode_options = models.JSONField(default=list, blank=True)
    default_params = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name


class StoreAssetType(models.Model):
    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=200)
    family = models.CharField(max_length=64, default="column")
    placement_mode_options = models.JSONField(default=list, blank=True)
    default_params = models.JSONField(default=dict, blank=True)
    participates_in_planogram = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name
