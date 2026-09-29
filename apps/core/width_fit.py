"""Shared width-fit helpers (D3 / A15 / A32 / A39)."""

from __future__ import annotations

from typing import Any, Iterable


def effective_width_mm(width_mm: int, height_mm: int, orientation: str) -> int:
    if orientation == "rotated_90":
        return int(height_mm or width_mm)
    return int(width_mm)


def available_width_mm(carrier_width_mm: int, reserved_insets_mm: int = 0) -> int:
    """D3: available_width = carrier.width_mm - sum(configured_reserved_insets_mm)."""
    return max(0, int(carrier_width_mm) - int(reserved_insets_mm or 0))


def width_consumed_mm(eff_width: int, facings: int) -> int:
    return int(eff_width) * max(1, int(facings))


def summarize_carrier(
    carrier_width_mm: int,
    reserved_insets_mm: int,
    placements: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    available = available_width_mm(carrier_width_mm, reserved_insets_mm)
    used = 0
    items = []
    for p in placements:
        eff = int(p.get("effective_width_mm") or 0)
        facings = int(p.get("facings") or 1)
        consumed = width_consumed_mm(eff, facings)
        used += consumed
        items.append({**p, "width_consumed_mm": consumed})
    remaining = available - used
    return {
        "available_width_mm": available,
        "used_width_mm": used,
        "remaining_width_mm": remaining,
        "overflow": remaining < 0,
        "placements": items,
    }


def validate_scene_width_fit(
    graph: dict[str, Any],
    carriers: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Re-validate width-fit for all carriers referenced in a scene graph.
    carriers keyed by component_instance_id (str) with width_mm / reserved_insets_mm.
    """
    issues: list[dict[str, Any]] = []
    placements = graph.get("placements") or []
    by_carrier: dict[str, list[dict[str, Any]]] = {}
    for p in placements:
        ref = p.get("carrier_ref") or {}
        cid = str(ref.get("component_instance_id") or "")
        if not cid:
            issues.append(
                {
                    "severity": "error",
                    "code": "missing_carrier",
                    "message": f"Placement {p.get('id')} missing carrier_ref.component_instance_id",
                }
            )
            continue
        by_carrier.setdefault(cid, []).append(p)

    for cid, plist in by_carrier.items():
        carrier = carriers.get(cid)
        if not carrier:
            issues.append(
                {
                    "severity": "error",
                    "code": "unknown_carrier",
                    "message": f"Carrier {cid} not found",
                    "carrier_id": cid,
                }
            )
            continue
        summary = summarize_carrier(
            carrier["width_mm"],
            carrier.get("reserved_insets_mm", 0),
            plist,
        )
        if summary["overflow"]:
            issues.append(
                {
                    "severity": "error",
                    "code": "width_overflow",
                    "message": (
                        f"Carrier {cid} overflow by "
                        f"{abs(summary['remaining_width_mm'])} mm"
                    ),
                    "carrier_id": cid,
                    "summary": summary,
                }
            )
    return issues
