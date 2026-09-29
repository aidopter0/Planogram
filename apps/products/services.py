"""Product CSV (+ optional ZIP images) import service."""

from __future__ import annotations

import csv
import io
import zipfile
from pathlib import Path
from typing import BinaryIO

from django.core.files.base import ContentFile

from apps.products.models import Orientation, Product, ProductImportJob, Readiness


REQUIRED_COLUMNS = {"sku", "name", "width_mm"}


def _norm(s: str) -> str:
    return (s or "").strip()


def import_products_csv(
    csv_file: BinaryIO,
    zip_file: BinaryIO | None = None,
) -> ProductImportJob:
    job = ProductImportJob.objects.create(state=ProductImportJob.State.PROCESSING)
    text = io.TextIOWrapper(csv_file, encoding="utf-8-sig", newline="")
    reader = csv.DictReader(text)
    if not reader.fieldnames:
        job.state = ProductImportJob.State.FAILED
        job.report = {"errors": ["CSV has no header row"]}
        job.save()
        return job

    cols = {c.strip().lower() for c in reader.fieldnames}
    missing = REQUIRED_COLUMNS - cols
    if missing:
        job.state = ProductImportJob.State.FAILED
        job.report = {"errors": [f"Missing columns: {sorted(missing)}"]}
        job.save()
        return job

    images: dict[str, bytes] = {}
    if zip_file is not None:
        with zipfile.ZipFile(zip_file) as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                stem = Path(info.filename).stem.lower()
                images[stem] = zf.read(info.filename)

    created = updated = errors = 0
    error_rows: list[dict] = []
    fieldmap = {c.strip().lower(): c for c in reader.fieldnames}

    def get(row: dict, key: str, default: str = "") -> str:
        return _norm(row.get(fieldmap.get(key, key), default))

    for i, row in enumerate(reader, start=2):
        sku = get(row, "sku")
        name = get(row, "name")
        try:
            width_mm = int(get(row, "width_mm") or "0")
        except ValueError:
            errors += 1
            error_rows.append({"row": i, "error": "width_mm must be integer"})
            continue
        if not sku or not name or width_mm <= 0:
            errors += 1
            error_rows.append({"row": i, "error": "sku, name, width_mm required"})
            continue

        try:
            height_mm = int(get(row, "height_mm") or "0")
            depth_mm = int(get(row, "depth_mm") or "0")
        except ValueError:
            errors += 1
            error_rows.append({"row": i, "error": "height_mm/depth_mm must be integers"})
            continue

        orient = get(row, "orientation", Orientation.NORMAL).lower() or Orientation.NORMAL
        if orient not in Orientation.values:
            orient = Orientation.NORMAL

        defaults = {
            "barcode": get(row, "barcode"),
            "name": name,
            "brand": get(row, "brand"),
            "category": get(row, "category"),
            "subcategory": get(row, "subcategory"),
            "width_mm": width_mm,
            "height_mm": height_mm,
            "depth_mm": depth_mm,
            "orientation": orient,
            "pack_type": get(row, "pack_type"),
        }
        product, was_created = Product.objects.update_or_create(
            sku=sku, defaults=defaults
        )
        if was_created:
            created += 1
        else:
            updated += 1

        img_bytes = images.get(sku.lower())
        if img_bytes:
            ext = ".jpg"
            product.front_image.save(
                f"{sku.lower()}{ext}", ContentFile(img_bytes), save=False
            )
            product.image_incomplete = False
            product.readiness = Readiness.IMAGE_COMPLETE
        else:
            product.image_incomplete = not bool(product.front_image)
            if product.width_mm > 0 and product.name:
                product.readiness = (
                    Readiness.ARRANGE_READY
                    if not product.image_incomplete
                    else Readiness.IMPORT_VALID
                )
        product.save()

    job.created_count = created
    job.updated_count = updated
    job.error_count = errors
    job.report = {"errors": error_rows[:50], "image_matches": len(images)}
    job.state = ProductImportJob.State.READY
    job.save()
    return job
