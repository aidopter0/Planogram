from django.db import models

from apps.catalog.models import FixtureComponentType, FixtureType, PlacementMode, StoreAssetType
from apps.layouts.models import StoreLayout
from apps.stores.models import Aisle, Department, Store


class FixtureRun(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="fixture_runs")
    layout = models.ForeignKey(
        StoreLayout, on_delete=models.CASCADE, related_name="fixture_runs"
    )
    name = models.CharField(max_length=120, blank=True, default="")
    bay_count = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name or f"Run {self.pk}"


class FixtureInstance(models.Model):
    """Store-local fixture placed on a Store Layout."""

    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="fixtures")
    layout = models.ForeignKey(
        StoreLayout, on_delete=models.CASCADE, related_name="fixtures"
    )
    fixture_type = models.ForeignKey(
        FixtureType, on_delete=models.PROTECT, related_name="instances"
    )
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="fixtures"
    )
    aisle = models.ForeignKey(
        Aisle, on_delete=models.SET_NULL, null=True, blank=True, related_name="fixtures"
    )
    run = models.ForeignKey(
        FixtureRun,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bays",
    )
    bay_index = models.PositiveIntegerField(default=0)
    name = models.CharField(max_length=120, blank=True, default="")
    # Pose in Source CAD coordinate system (mm) — floor/top is SoT (D2).
    x_mm = models.IntegerField(default=0)
    y_mm = models.IntegerField(default=0)
    rotation_deg = models.FloatField(default=0.0)
    params = models.JSONField(default=dict, blank=True)
    placement_mode = models.CharField(
        max_length=32, choices=PlacementMode.choices, default=PlacementMode.FLOOR
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["run_id", "bay_index", "id"]

    def __str__(self) -> str:
        return self.name or f"{self.fixture_type.code}-{self.pk}"

    @property
    def bay_width_mm(self) -> int:
        if "bay_width_mm" in self.params:
            return int(self.params["bay_width_mm"])
        return int(self.fixture_type.default_params.get("bay_width_mm", 900))


class ComponentInstance(models.Model):
    """Carrier-capable component attached to a fixture (e.g. shelf)."""

    fixture = models.ForeignKey(
        FixtureInstance, on_delete=models.CASCADE, related_name="components"
    )
    component_type = models.ForeignKey(
        FixtureComponentType, on_delete=models.PROTECT, related_name="instances"
    )
    face = models.CharField(max_length=8, default="A")
    shelf_index = models.PositiveIntegerField(default=0)
    height_mm = models.IntegerField(default=0)
    width_mm = models.PositiveIntegerField(default=900)
    depth_mm = models.PositiveIntegerField(default=400)
    reserved_insets_mm = models.PositiveIntegerField(default=0)
    params = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["face", "shelf_index", "id"]

    def __str__(self) -> str:
        return f"{self.fixture_id}/{self.face}/S{self.shelf_index}"

    @property
    def available_width_mm(self) -> int:
        """D3: available_width = carrier.width_mm - sum(configured_reserved_insets_mm)."""
        inset = self.reserved_insets_mm
        if inset == 0 and self.component_type_id:
            inset = self.component_type.reserved_inset_mm
        return max(0, self.width_mm - inset)


class StoreAssetInstance(models.Model):
    """Store-local environment / visualization asset on a Store Layout."""

    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="store_assets")
    layout = models.ForeignKey(
        StoreLayout, on_delete=models.CASCADE, related_name="store_assets"
    )
    asset_type = models.ForeignKey(
        StoreAssetType, on_delete=models.PROTECT, related_name="instances"
    )
    name = models.CharField(max_length=120, blank=True, default="")
    x_mm = models.IntegerField(default=0)
    y_mm = models.IntegerField(default=0)
    rotation_deg = models.FloatField(default=0.0)
    params = models.JSONField(default=dict, blank=True)
    placement_mode = models.CharField(
        max_length=32, choices=PlacementMode.choices, default=PlacementMode.FLOOR
    )
    source = models.CharField(
        max_length=16,
        choices=[("library", "Library"), ("cad_extract", "CAD extract")],
        default="library",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return self.name or f"{self.asset_type.code}-{self.pk}"

    @property
    def participates_in_planogram(self) -> bool:
        return bool(self.asset_type.participates_in_planogram)
