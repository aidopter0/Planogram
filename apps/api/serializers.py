from rest_framework import serializers

from apps.catalog.models import (
    DisplayAssetType,
    FixtureComponentType,
    FixtureType,
    StoreAssetType,
)
from apps.fixtures.models import (
    ComponentInstance,
    FixtureInstance,
    FixtureRun,
    StoreAssetInstance,
)
from apps.layouts.models import StoreLayout
from apps.planograms.models import Planogram, PlanogramScene
from apps.products.models import Product
from apps.stores.models import Aisle, Department, Store


class StoreSerializer(serializers.ModelSerializer):
    active_layout_id = serializers.SerializerMethodField()

    class Meta:
        model = Store
        fields = [
            "id",
            "name",
            "code",
            "cluster_tag",
            "status",
            "active_layout_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "active_layout_id"]

    def get_active_layout_id(self, obj: Store) -> int | None:
        layout = obj.layouts.filter(is_active=True).first()
        return layout.id if layout else None


class StoreLayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreLayout
        fields = [
            "id",
            "store",
            "name",
            "is_active",
            "source_format",
            "source_filename",
            "units",
            "scale_factor",
            "origin_offset_x_mm",
            "origin_offset_y_mm",
            "rotation_deg",
            "status",
            "confidence_pct",
            "needs_review_counts",
            "overlays",
            "underlay",
            "extent_min_x",
            "extent_min_y",
            "extent_max_x",
            "extent_max_y",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
            "underlay",
            "confidence_pct",
            "needs_review_counts",
            "source_format",
            "source_filename",
            "extent_min_x",
            "extent_min_y",
            "extent_max_x",
            "extent_max_y",
            "status",
        ]


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id", "store", "name", "code", "sort_order", "cad_seeded"]


class AisleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aisle
        fields = ["id", "store", "department", "name", "number"]


class FixtureTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FixtureType
        fields = [
            "id",
            "code",
            "name",
            "family",
            "tier",
            "default_params",
            "param_schema",
            "placement_mode_options",
            "is_active",
        ]


class FixtureComponentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FixtureComponentType
        fields = [
            "id",
            "code",
            "name",
            "family",
            "default_params",
            "placement_mode_options",
            "reserved_inset_mm",
            "is_active",
        ]


class DisplayAssetTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DisplayAssetType
        fields = [
            "id",
            "code",
            "name",
            "family",
            "placement_mode_options",
            "default_params",
            "is_active",
        ]


class StoreAssetTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreAssetType
        fields = [
            "id",
            "code",
            "name",
            "family",
            "placement_mode_options",
            "default_params",
            "participates_in_planogram",
            "is_active",
        ]


class StoreAssetInstanceSerializer(serializers.ModelSerializer):
    asset_type_code = serializers.CharField(source="asset_type.code", read_only=True)
    asset_type_name = serializers.CharField(source="asset_type.name", read_only=True)
    asset_type_family = serializers.CharField(source="asset_type.family", read_only=True)
    participates_in_planogram = serializers.BooleanField(read_only=True)

    class Meta:
        model = StoreAssetInstance
        fields = [
            "id",
            "store",
            "layout",
            "asset_type",
            "asset_type_code",
            "asset_type_name",
            "asset_type_family",
            "name",
            "x_mm",
            "y_mm",
            "rotation_deg",
            "params",
            "placement_mode",
            "source",
            "participates_in_planogram",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class ComponentInstanceSerializer(serializers.ModelSerializer):
    available_width_mm = serializers.IntegerField(read_only=True)
    component_type_code = serializers.CharField(
        source="component_type.code", read_only=True
    )

    class Meta:
        model = ComponentInstance
        fields = [
            "id",
            "fixture",
            "component_type",
            "component_type_code",
            "face",
            "shelf_index",
            "height_mm",
            "width_mm",
            "depth_mm",
            "reserved_insets_mm",
            "available_width_mm",
            "params",
        ]


class FixtureInstanceSerializer(serializers.ModelSerializer):
    fixture_type_code = serializers.CharField(source="fixture_type.code", read_only=True)
    fixture_type_name = serializers.CharField(source="fixture_type.name", read_only=True)
    fixture_type_family = serializers.CharField(source="fixture_type.family", read_only=True)
    components = ComponentInstanceSerializer(many=True, read_only=True)
    bay_width_mm = serializers.IntegerField(read_only=True)

    class Meta:
        model = FixtureInstance
        fields = [
            "id",
            "store",
            "layout",
            "fixture_type",
            "fixture_type_code",
            "fixture_type_name",
            "fixture_type_family",
            "department",
            "aisle",
            "run",
            "bay_index",
            "name",
            "x_mm",
            "y_mm",
            "rotation_deg",
            "params",
            "placement_mode",
            "bay_width_mm",
            "components",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class FixtureRunSerializer(serializers.ModelSerializer):
    bays = FixtureInstanceSerializer(many=True, read_only=True)

    class Meta:
        model = FixtureRun
        fields = ["id", "store", "layout", "name", "bay_count", "bays", "created_at"]
        read_only_fields = ["created_at"]


class ProductSerializer(serializers.ModelSerializer):
    front_image_url = serializers.SerializerMethodField()
    effective_width_mm = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "sku",
            "barcode",
            "name",
            "brand",
            "category",
            "subcategory",
            "width_mm",
            "height_mm",
            "depth_mm",
            "orientation",
            "front_image",
            "front_image_url",
            "effective_width_mm",
            "pack_type",
            "image_incomplete",
            "readiness",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "image_incomplete", "readiness"]

    def get_front_image_url(self, obj: Product) -> str | None:
        if obj.front_image:
            request = self.context.get("request")
            url = obj.front_image.url
            if request:
                return request.build_absolute_uri(url)
            return url
        return None

    def get_effective_width_mm(self, obj: Product) -> int:
        return obj.effective_width_mm()


class PlanogramSceneSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanogramScene
        fields = ["schema_version", "graph", "updated_at"]
        read_only_fields = ["updated_at"]


class PlanogramSerializer(serializers.ModelSerializer):
    scene = PlanogramSceneSerializer(read_only=True)

    class Meta:
        model = Planogram
        fields = [
            "id",
            "store",
            "name",
            "status",
            "tags",
            "target_fixture_ids",
            "owner",
            "scene",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "owner"]
