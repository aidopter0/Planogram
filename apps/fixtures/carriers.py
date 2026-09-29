"""Helpers for store-local fixture carriers."""

from __future__ import annotations

from apps.catalog.models import FixtureComponentType, FixtureType
from apps.fixtures.models import ComponentInstance, FixtureInstance

# Families that hold product even without explicit shelf_count (bin / table / well).
MERCHANDISING_FAMILIES = {
    "gondola",
    "produce",
    "chilled",
    "frozen",
    "bakery",
    "deli",
    "bulk",
    "checkout",
}


def _ensure_component_types() -> tuple[FixtureComponentType | None, FixtureComponentType | None]:
    shelf, _ = FixtureComponentType.objects.get_or_create(
        code="SHELF_STD",
        defaults={
            "name": "Standard shelf/board",
            "family": "shelf",
            "default_params": {"depth_mm": 400},
            "placement_mode_options": ["ATTACHED", "SHELF"],
            "reserved_inset_mm": 0,
            "is_active": True,
        },
    )
    well, _ = FixtureComponentType.objects.get_or_create(
        code="WELL",
        defaults={
            "name": "Merchandising well / surface",
            "family": "well",
            "default_params": {},
            "placement_mode_options": ["FLOOR", "SHELF"],
            "reserved_inset_mm": 0,
            "is_active": True,
        },
    )
    return shelf, well


def create_carriers_for_instance(inst: FixtureInstance) -> list[ComponentInstance]:
    """
    Create shelf and/or well carriers from fixture type params.
    If shelf_count > 0 → shelves. Else if merchandising family → one WELL surface.
    """
    if inst.components.exists():
        return list(inst.components.all())

    ftype: FixtureType = inst.fixture_type
    params = {**(ftype.default_params or {}), **(inst.params or {})}
    bay_width = int(params.get("bay_width_mm", 900))
    shelf_count = int(params.get("shelf_count", 0))
    shelf_depth = int(params.get("shelf_depth_mm", params.get("depth_mm", 400)))
    shelf_pitch = int(params.get("shelf_pitch_mm", 350))
    shelf_type, well_type = _ensure_component_types()
    created: list[ComponentInstance] = []

    if shelf_type and shelf_count > 0:
        for i in range(shelf_count):
            created.append(
                ComponentInstance.objects.create(
                    fixture=inst,
                    component_type=shelf_type,
                    face="A",
                    shelf_index=i,
                    height_mm=200 + i * shelf_pitch,
                    width_mm=bay_width,
                    depth_mm=shelf_depth,
                    reserved_insets_mm=0,
                )
            )
    elif well_type and ftype.family in MERCHANDISING_FAMILIES:
        created.append(
            ComponentInstance.objects.create(
                fixture=inst,
                component_type=well_type,
                face="A",
                shelf_index=0,
                height_mm=int(params.get("height_mm", 700)) // 2,
                width_mm=bay_width,
                depth_mm=int(params.get("depth_mm", shelf_depth)),
                reserved_insets_mm=0,
                params={"kind": "well"},
            )
        )
    return created
