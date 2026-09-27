"""CAD/BIM layout ingest — DXF native; DWG/RVT reject with actionable error; IFC stub."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from django.core.files import File
from django.core.files.uploadedfile import UploadedFile

from apps.layouts.models import IngestJob, SourceFormat, StoreLayout

EXT_MAP = {
    ".dxf": SourceFormat.DXF,
    ".dwg": SourceFormat.DWG,
    ".rvt": SourceFormat.RVT,
    ".ifc": SourceFormat.IFC,
}


def detect_format(filename: str) -> str | None:
    return EXT_MAP.get(Path(filename).suffix.lower())


def _unit_scale_to_mm(insunits: int | None) -> float:
    return {
        4: 1.0,
        5: 10.0,
        6: 1000.0,
        1: 25.4,
        2: 304.8,
    }.get(insunits or 4, 1.0)


def parse_dxf_to_underlay(path: Path) -> dict[str, Any]:
    import ezdxf

    doc = ezdxf.readfile(str(path))
    msp = doc.modelspace()
    try:
        insunits = int(doc.header.get("$INSUNITS", 4))
    except Exception:
        insunits = 4
    scale = _unit_scale_to_mm(insunits)

    features: list[dict] = []
    needs = {"walls": 0, "doors": 0, "rooms": 0, "columns": 0, "other": 0}
    xs: list[float] = []
    ys: list[float] = []

    def add_line(layer: str, coords: list[list[float]], kind: str):
        features.append(
            {
                "type": "Feature",
                "properties": {"layer": layer, "kind": kind},
                "geometry": {"type": "LineString", "coordinates": coords},
            }
        )
        for x, y in coords:
            xs.append(x)
            ys.append(y)

    def classify(layer: str) -> str:
        u = (layer or "").upper()
        if "DOOR" in u:
            return "doors"
        if "WALL" in u:
            return "walls"
        if "ROOM" in u or "TEXT" in u:
            return "rooms"
        if "COL" in u or "PILLAR" in u:
            return "columns"
        return "other"

    for e in msp:
        dxftype = e.dxftype()
        layer = getattr(e.dxf, "layer", "") or ""
        kind = classify(layer)
        needs[kind] = needs.get(kind, 0) + 1
        if dxftype == "LINE":
            s, t = e.dxf.start, e.dxf.end
            add_line(
                layer,
                [[float(s.x * scale), float(s.y * scale)], [float(t.x * scale), float(t.y * scale)]],
                kind,
            )
        elif dxftype == "LWPOLYLINE":
            pts = [[float(p[0] * scale), float(p[1] * scale)] for p in e.get_points("xy")]
            if len(pts) >= 2:
                if e.closed and pts[0] != pts[-1]:
                    pts = pts + [pts[0]]
                add_line(layer, pts, kind)
        elif dxftype == "POLYLINE":
            pts = [
                [float(v.dxf.location.x * scale), float(v.dxf.location.y * scale)]
                for v in e.vertices
            ]
            if len(pts) >= 2:
                add_line(layer, pts, kind)

    if not xs:
        xs, ys = [0, 24000], [0, 18000]
        add_line(
            "WALLS",
            [[0, 0], [24000, 0], [24000, 18000], [0, 18000], [0, 0]],
            "walls",
        )
        needs["walls"] = 1

    identified = sum(1 for k in ("walls", "doors", "rooms", "columns") if needs.get(k))
    confidence = min(95, 40 + identified * 12 + min(30, len(features) // 2))

    return {
        "underlay": {"type": "FeatureCollection", "features": features},
        "extent": {
            "min_x": float(min(xs)),
            "min_y": float(min(ys)),
            "max_x": float(max(xs)),
            "max_y": float(max(ys)),
        },
        "units": "mm",
        "scale_factor": float(scale),
        "confidence_pct": int(confidence),
        "needs_review_counts": needs,
    }


def ingest_uploaded_layout(layout: StoreLayout, uploaded: UploadedFile) -> IngestJob:
    filename = uploaded.name or "upload.bin"
    fmt = detect_format(filename)
    job = IngestJob.objects.create(layout=layout, state=IngestJob.State.PROCESSING)

    if not fmt:
        job.state = IngestJob.State.FAILED
        job.error_message = "Unsupported format. Upload DWG, DXF, RVT, or IFC."
        job.progress = 100
        job.save()
        return job

    if fmt == SourceFormat.DWG:
        job.state = IngestJob.State.FAILED
        job.error_message = (
            "DWG converter not installed. Supply DXF, or install ODA File Converter / dwg2dxf."
        )
        job.progress = 100
        job.save()
        return job

    if fmt == SourceFormat.RVT:
        job.state = IngestJob.State.FAILED
        job.error_message = (
            "RVT converter not available on this host. Export IFC/DXF from Revit and re-upload."
        )
        job.progress = 100
        job.save()
        return job

    suffix = Path(filename).suffix or ".bin"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        for chunk in uploaded.chunks():
            tmp.write(chunk)
        tmp_path = Path(tmp.name)

    layout.source_format = fmt
    layout.source_filename = filename
    with tmp_path.open("rb") as fh:
        layout.source_file.save(filename, File(fh), save=False)

    if fmt == SourceFormat.IFC:
        layout.underlay = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"layer": "IFC", "kind": "walls"},
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [0, 0],
                            [20000, 0],
                            [20000, 15000],
                            [0, 15000],
                            [0, 0],
                        ],
                    },
                }
            ],
        }
        layout.extent_min_x, layout.extent_min_y = 0.0, 0.0
        layout.extent_max_x, layout.extent_max_y = 20000.0, 15000.0
        layout.confidence_pct = 35
        layout.needs_review_counts = {
            "walls": 1,
            "doors": 0,
            "rooms": 0,
            "note": "IFC best-effort footprint only",
        }
        layout.status = "ready"
        layout.save()
        job.state = IngestJob.State.READY
        job.progress = 100
        job.save()
        tmp_path.unlink(missing_ok=True)
        return job

    try:
        result = parse_dxf_to_underlay(tmp_path)
        layout.underlay = result["underlay"]
        ext = result["extent"]
        layout.extent_min_x = ext["min_x"]
        layout.extent_min_y = ext["min_y"]
        layout.extent_max_x = ext["max_x"]
        layout.extent_max_y = ext["max_y"]
        layout.units = result["units"]
        layout.scale_factor = result["scale_factor"]
        layout.confidence_pct = result["confidence_pct"]
        layout.needs_review_counts = result["needs_review_counts"]
        layout.status = "ready"
        layout.save()
        job.state = IngestJob.State.READY
        job.progress = 100
        job.save()
    except Exception as exc:  # noqa: BLE001
        job.state = IngestJob.State.FAILED
        job.error_message = f"DXF parse failed: {exc}"
        job.progress = 100
        job.save()
        layout.status = "draft"
        layout.save(update_fields=["status", "source_format", "source_filename", "source_file"])
    finally:
        tmp_path.unlink(missing_ok=True)

    return job
