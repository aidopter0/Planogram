"""Seed demo org: users, catalog, store, fixtures, sample products."""

from __future__ import annotations

import csv
import io
import zipfile
from pathlib import Path

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from PIL import Image, ImageDraw, ImageFont

from apps.accounts.models import OrgSettings, Profile, Role
from apps.catalog.models import (
    DisplayAssetType,
    FixtureComponentType,
    FixtureType,
    PlacementMode,
    StoreAssetType,
)
from apps.fixtures.models import ComponentInstance, FixtureInstance, FixtureRun
from apps.layouts.models import StoreLayout
from apps.planograms.models import Planogram, PlanogramScene
from apps.products.models import Product, Readiness
from apps.products.services import import_products_csv
from apps.stores.models import Aisle, Department, Store, StoreStatus

FIXTURES_ROOT = Path(__file__).resolve().parents[4] / "fixtures"


SAMPLE_PRODUCTS = [
    # sku, name, brand, category, w, h, d
    ("COLA500", "Cola Classic 500 ml", "FizzCo", "Beverages", 66, 220, 66),
    ("COLA330", "Cola Classic 330 ml", "FizzCo", "Beverages", 58, 115, 58),
    ("WATER1500", "Spring Water 1.5 L", "ClearSpring", "Beverages", 85, 300, 85),
    ("CHIPS150", "Salted Chips 150 g", "CrunchFarm", "Snacks", 80, 220, 50),
    ("CHIPS40", "Salted Chips 40 g", "CrunchFarm", "Snacks", 50, 140, 30),
    ("OATS500", "Rolled Oats 500 g", "MorningMill", "Breakfast", 95, 180, 60),
    ("MILK1L", "Whole Milk 1 L", "DairyHill", "Dairy", 70, 230, 70),
    ("YOG125", "Greek Yogurt 125 g", "DairyHill", "Dairy", 75, 75, 75),
    ("PASTA500", "Spaghetti 500 g", "PastaRoma", "Grocery", 50, 280, 30),
    ("RICE1KG", "Long Grain Rice 1 kg", "GrainField", "Grocery", 100, 200, 60),
    ("SOAP200", "Bar Soap 200 g", "CleanHome", "HBA", 90, 60, 40),
    ("SHAM400", "Shampoo 400 ml", "CleanHome", "HBA", 70, 200, 50),
]


def _placeholder_png(sku: str, name: str, color: tuple[int, int, int]) -> bytes:
    img = Image.new("RGB", (240, 320), color)
    draw = ImageDraw.Draw(img)
    draw.rectangle([12, 12, 228, 308], outline=(255, 255, 255), width=3)
    # Simple text — default font
    draw.text((24, 40), sku[:12], fill=(255, 255, 255))
    # Wrap name roughly
    words = name.split()
    lines, line = [], ""
    for w in words:
        trial = f"{line} {w}".strip()
        if len(trial) > 16:
            lines.append(line)
            line = w
        else:
            line = trial
    if line:
        lines.append(line)
    y = 120
    for ln in lines[:4]:
        draw.text((24, y), ln, fill=(255, 255, 255))
        y += 28
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


COLORS = [
    (16, 185, 129),
    (14, 165, 233),
    (245, 158, 11),
    (244, 63, 94),
    (100, 116, 139),
    (52, 211, 153),
]


class Command(BaseCommand):
    help = "Seed Planogram demo data (catalog, store, products, sample planogram)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--from-fixtures",
            action="store_true",
            help="Also import fixtures/products/products.csv + images.zip if present",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        OrgSettings.load()
        self._users()
        self._catalog()
        store = self._store()
        self._products(options.get("from_fixtures"))
        self._planogram(store)
        self.stdout.write(self.style.SUCCESS("Seed complete."))
        self.stdout.write("  Login: designer / designer123  (or admin / admin123)")

    def _users(self):
        specs = [
            ("admin", "admin123", Role.ADMIN, True),
            ("designer", "designer123", Role.DESIGNER, False),
            ("steward", "steward123", Role.PRODUCT_STEWARD, False),
            ("viewer", "viewer123", Role.VIEWER, False),
            ("catalog", "catalog123", Role.CATALOG_ADMIN, False),
        ]
        for username, password, role, is_super in specs:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"is_staff": is_super or role == Role.ADMIN, "is_superuser": is_super},
            )
            if created:
                user.set_password(password)
                user.save()
            Profile.objects.update_or_create(user=user, defaults={"role": role})
            self.stdout.write(f"  user {username} ({role})")

    def _catalog(self):
        gondola, _ = FixtureType.objects.update_or_create(
            code="GONDOLA_900",
            defaults={
                "name": "Standard Gondola 900 mm",
                "family": "gondola",
                "tier": 1,
                "default_params": {
                    "bay_width_mm": 900,
                    "height_mm": 1600,
                    "depth_mm": 450,
                    "shelf_count": 4,
                    "shelf_pitch_mm": 350,
                    "shelf_depth_mm": 400,
                    "faces": 2,
                },
                "placement_mode_options": [PlacementMode.FLOOR],
                "is_active": True,
            },
        )
        FixtureType.objects.update_or_create(
            code="CHILLER_MULTIDECK",
            defaults={
                "name": "Open Multideck Chiller",
                "family": "frozen",
                "tier": 1,
                "default_params": {
                    "bay_width_mm": 1250,
                    "height_mm": 2000,
                    "depth_mm": 900,
                    "shelf_count": 5,
                    "shelf_pitch_mm": 300,
                    "shelf_depth_mm": 500,
                    "faces": 1,
                },
                "placement_mode_options": [PlacementMode.FLOOR],
                "is_active": True,
            },
        )
        FixtureComponentType.objects.update_or_create(
            code="SHELF_STD",
            defaults={
                "name": "Standard Shelf",
                "family": "shelf",
                "default_params": {"depth_mm": 400},
                "placement_mode_options": [PlacementMode.ATTACHED, PlacementMode.SHELF],
                "reserved_inset_mm": 0,
                "is_active": True,
            },
        )
        FixtureComponentType.objects.update_or_create(
            code="DIVIDER",
            defaults={
                "name": "Shelf Divider",
                "family": "divider",
                "default_params": {},
                "placement_mode_options": [PlacementMode.SHELF],
                "reserved_inset_mm": 10,
                "is_active": True,
            },
        )
        DisplayAssetType.objects.update_or_create(
            code="ENDCAP",
            defaults={
                "name": "Endcap Display",
                "family": "endcap",
                "placement_mode_options": [
                    PlacementMode.FLOOR,
                    PlacementMode.FIXTURE_FACE,
                ],
                "is_active": True,
            },
        )
        StoreAssetType.objects.update_or_create(
            code="COLUMN",
            defaults={
                "name": "Structural Column",
                "family": "column",
                "placement_mode_options": [PlacementMode.FLOOR],
                "participates_in_planogram": False,
                "is_active": True,
            },
        )
        self.stdout.write(f"  catalog seeded (gondola id={gondola.id})")

    def _store(self) -> Store:
        store, _ = Store.objects.update_or_create(
            code="COASTAL-01",
            defaults={
                "name": "Coastal Market — Draft",
                "cluster_tag": "coastal",
                "status": StoreStatus.DRAFT,
            },
        )
        layout, _ = StoreLayout.objects.update_or_create(
            store=store,
            is_active=True,
            defaults={
                "name": "Active layout",
                "source_format": "dxf",
                "source_filename": "sample-store.dxf",
                "status": "ready",
                "confidence_pct": 72,
                "needs_review_counts": {"walls": 2, "doors": 1, "rooms": 0},
            },
        )
        grocery, _ = Department.objects.update_or_create(
            store=store, name="Grocery", defaults={"code": "GRO", "sort_order": 1}
        )
        beverages, _ = Department.objects.update_or_create(
            store=store, name="Beverages", defaults={"code": "BEV", "sort_order": 2}
        )
        aisle, _ = Aisle.objects.update_or_create(
            store=store,
            name="Aisle 7",
            defaults={"department": grocery, "number": 7},
        )
        gondola = FixtureType.objects.get(code="GONDOLA_900")
        shelf = FixtureComponentType.objects.get(code="SHELF_STD")
        if not store.fixtures.exists():
            run = FixtureRun.objects.create(
                store=store, layout=layout, name="Aisle 7 Gondola Run", bay_count=4
            )
            for i in range(4):
                inst = FixtureInstance.objects.create(
                    store=store,
                    layout=layout,
                    fixture_type=gondola,
                    department=grocery if i < 3 else beverages,
                    aisle=aisle,
                    run=run,
                    bay_index=i,
                    name=f"GONDOLA_900-B{i + 1}",
                    x_mm=i * 900,
                    y_mm=0,
                    params=dict(gondola.default_params),
                )
                for s in range(4):
                    ComponentInstance.objects.create(
                        fixture=inst,
                        component_type=shelf,
                        face="A",
                        shelf_index=s,
                        height_mm=200 + s * 350,
                        width_mm=900,
                        depth_mm=400,
                    )
        self.stdout.write(f"  store {store.name} (id={store.id})")
        return store

    def _products(self, from_fixtures: bool):
        products_dir = FIXTURES_ROOT / "products"
        csv_path = products_dir / "products.csv"
        zip_path = products_dir / "images.zip"

        if from_fixtures and csv_path.exists():
            with csv_path.open("rb") as cf:
                zf = zip_path.open("rb") if zip_path.exists() else None
                try:
                    job = import_products_csv(cf, zf)
                    self.stdout.write(
                        f"  imported fixtures CSV: +{job.created_count} ~{job.updated_count}"
                    )
                finally:
                    if zf:
                        zf.close()
            return

        # Generate synthetic pack fronts + products
        products_dir.mkdir(parents=True, exist_ok=True)
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            writer_rows = []
            for idx, (sku, name, brand, cat, w, h, d) in enumerate(SAMPLE_PRODUCTS):
                png = _placeholder_png(sku, name, COLORS[idx % len(COLORS)])
                zf.writestr(f"{sku}.png", png)
                writer_rows.append(
                    {
                        "sku": sku,
                        "name": name,
                        "brand": brand,
                        "category": cat,
                        "width_mm": w,
                        "height_mm": h,
                        "depth_mm": d,
                        "orientation": "normal",
                        "barcode": f"0000000{idx:05d}",
                    }
                )
        zip_buf.seek(0)

        # Write CSV + ZIP into fixtures/ for D5
        with (products_dir / "products.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "sku",
                    "name",
                    "brand",
                    "category",
                    "width_mm",
                    "height_mm",
                    "depth_mm",
                    "orientation",
                    "barcode",
                ],
            )
            writer.writeheader()
            writer.writerows(writer_rows)
        (products_dir / "images.zip").write_bytes(zip_buf.getvalue())

        zip_buf.seek(0)
        with (products_dir / "products.csv").open("rb") as cf:
            job = import_products_csv(cf, zip_buf)
        self.stdout.write(
            f"  products seeded: +{job.created_count} ~{job.updated_count} err={job.error_count}"
        )

    def _planogram(self, store: Store):
        bay = store.fixtures.order_by("bay_index").first()
        if not bay:
            return
        pog, _ = Planogram.objects.update_or_create(
            store=store,
            name="Aisle 7 Bay 1 — Draft",
            defaults={
                "status": "draft",
                "target_fixture_ids": [bay.id],
            },
        )
        carrier = bay.components.filter(shelf_index=2).first() or bay.components.first()
        products = list(Product.objects.filter(sku__in=["COLA500", "COLA330", "WATER1500"]))
        placements = []
        seq = 0
        used = 0
        if carrier:
            for prod, facings in zip(products, [4, 3, 2]):
                eff = prod.effective_width_mm()
                consumed = eff * facings
                if used + consumed > carrier.available_width_mm:
                    break
                placements.append(
                    {
                        "id": f"seed-{prod.sku}",
                        "product_id": prod.id,
                        "sku": prod.sku,
                        "carrier_ref": {
                            "fixture_instance_id": bay.id,
                            "component_instance_id": carrier.id,
                            "kind": "shelf",
                            "face": carrier.face,
                            "index": carrier.shelf_index,
                        },
                        "facings": facings,
                        "sequence": seq,
                        "orientation": prod.orientation,
                        "effective_width_mm": eff,
                        "width_consumed_mm": consumed,
                    }
                )
                used += consumed
                seq += 1
        PlanogramScene.objects.update_or_create(
            planogram=pog,
            defaults={
                "schema_version": 5,
                "graph": {
                    "schema_version": 5,
                    "units": "mm",
                    "blocks": [],
                    "placements": placements,
                },
            },
        )
        self.stdout.write(f"  planogram {pog.name} with {len(placements)} placements")
