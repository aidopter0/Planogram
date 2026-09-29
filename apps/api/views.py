from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.serializers import (
    AisleSerializer,
    ComponentInstanceSerializer,
    DepartmentSerializer,
    DisplayAssetTypeSerializer,
    FixtureComponentTypeSerializer,
    FixtureInstanceSerializer,
    FixtureRunSerializer,
    FixtureTypeSerializer,
    PlanogramSerializer,
    ProductSerializer,
    StoreAssetInstanceSerializer,
    StoreAssetTypeSerializer,
    StoreLayoutSerializer,
    StoreSerializer,
)
from apps.catalog.models import (
    DisplayAssetType,
    FixtureComponentType,
    FixtureType,
    PlacementMode,
    StoreAssetType,
)
from apps.catalog.seed_data import FAMILY_LABELS
from apps.core.width_fit import (
    effective_width_mm,
    summarize_carrier,
    validate_scene_width_fit,
)
from apps.fixtures.carriers import create_carriers_for_instance
from apps.fixtures.models import (
    ComponentInstance,
    FixtureInstance,
    FixtureRun,
    StoreAssetInstance,
)
from apps.layouts.models import StoreLayout
from apps.layouts.services import ingest_uploaded_layout
from apps.planograms.models import Planogram, PlanogramScene
from apps.products.models import Product
from apps.products.services import import_products_csv
from apps.stores.models import Aisle, Department, Store



@api_view(["GET"])
@permission_classes([AllowAny])
def healthz(request):
    return Response({"status": "ok", "service": "planogram"})


class StoreViewSet(viewsets.ModelViewSet):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer

    @action(detail=True, methods=["get"])
    def departments(self, request, pk=None):
        store = self.get_object()
        qs = store.departments.all()
        return Response(DepartmentSerializer(qs, many=True).data)

    @action(detail=True, methods=["get"])
    def aisles(self, request, pk=None):
        store = self.get_object()
        qs = store.aisles.all()
        return Response(AisleSerializer(qs, many=True).data)

    @action(detail=True, methods=["get"])
    def layout(self, request, pk=None):
        store = self.get_object()
        layout = store.layouts.filter(is_active=True).first()
        if not layout:
            return Response({"detail": "No active layout"}, status=404)
        return Response(StoreLayoutSerializer(layout).data)

    @action(detail=False, methods=["post"], url_path="create-with-layout")
    def create_with_layout(self, request):
        """New Store → CAD upload first. Creates store + active layout + ingest."""
        upload = request.FILES.get("file") or request.FILES.get("layout")
        if not upload:
            return Response(
                {"detail": "CAD/BIM file required (DWG/DXF/RVT/IFC)."},
                status=400,
            )
        name = (
            request.data.get("name")
            or Path(upload.name).stem.replace("_", " ").replace("-", " ").title()
            or "New Store"
        )
        code = request.data.get("code") or f"ST-{timezone.now().strftime('%H%M%S')}"
        with transaction.atomic():
            store = Store.objects.create(
                name=name,
                code=code,
                status=request.data.get("status") or "draft",
                cluster_tag=request.data.get("cluster_tag") or "",
            )
            # Deactivate any prior (none yet) and create active layout
            layout = StoreLayout.objects.create(
                store=store,
                name="Active layout",
                is_active=True,
                status="draft",
            )
            job = ingest_uploaded_layout(layout, upload)
            layout.refresh_from_db()
        return Response(
            {
                "store": StoreSerializer(store).data,
                "layout": StoreLayoutSerializer(layout).data,
                "ingest": {
                    "id": job.id,
                    "state": job.state,
                    "progress": job.progress,
                    "error_message": job.error_message,
                },
            },
            status=201 if job.state == "ready" else 400,
        )

    @action(detail=True, methods=["post"], url_path="upload-layout")
    def upload_layout(self, request, pk=None):
        store = self.get_object()
        upload = request.FILES.get("file") or request.FILES.get("layout")
        if not upload:
            return Response({"detail": "CAD/BIM file required"}, status=400)
        with transaction.atomic():
            store.layouts.filter(is_active=True).update(is_active=False)
            layout = StoreLayout.objects.create(
                store=store, name="Active layout", is_active=True, status="draft"
            )
            job = ingest_uploaded_layout(layout, upload)
            layout.refresh_from_db()
        return Response(
            {
                "layout": StoreLayoutSerializer(layout).data,
                "ingest": {
                    "id": job.id,
                    "state": job.state,
                    "progress": job.progress,
                    "error_message": job.error_message,
                },
            },
            status=200 if job.state == "ready" else 400,
        )


class StoreLayoutViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StoreLayout.objects.select_related("store")
    serializer_class = StoreLayoutSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        store_id = self.request.query_params.get("store")
        if store_id:
            qs = qs.filter(store_id=store_id)
        if self.request.query_params.get("active") == "1":
            qs = qs.filter(is_active=True)
        return qs


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.select_related("store")
    serializer_class = DepartmentSerializer


class AisleViewSet(viewsets.ModelViewSet):
    queryset = Aisle.objects.select_related("store", "department")
    serializer_class = AisleSerializer


class FixtureTypeViewSet(viewsets.ModelViewSet):
    serializer_class = FixtureTypeSerializer

    def get_queryset(self):
        qs = FixtureType.objects.filter(is_active=True)
        family = self.request.query_params.get("family")
        if family:
            qs = qs.filter(family=family)
        q = self.request.query_params.get("q")
        if q:
            from django.db.models import Q

            qs = qs.filter(Q(name__icontains=q) | Q(code__icontains=q))
        tier = self.request.query_params.get("tier")
        if tier:
            qs = qs.filter(tier=tier)
        return qs

    @action(detail=False, methods=["get"])
    def families(self, request):
        rows = (
            FixtureType.objects.filter(is_active=True)
            .values_list("family")
            .order_by("family")
            .distinct()
        )
        families = []
        for (fam,) in rows:
            families.append(
                {
                    "family": fam,
                    "label": FAMILY_LABELS.get(fam, fam.replace("_", " ").title()),
                    "count": FixtureType.objects.filter(is_active=True, family=fam).count(),
                }
            )
        return Response(families)


class FixtureComponentTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FixtureComponentType.objects.filter(is_active=True)
    serializer_class = FixtureComponentTypeSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        family = self.request.query_params.get("family")
        if family:
            qs = qs.filter(family=family)
        return qs


class DisplayAssetTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DisplayAssetType.objects.filter(is_active=True)
    serializer_class = DisplayAssetTypeSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        family = self.request.query_params.get("family")
        if family:
            qs = qs.filter(family=family)
        return qs


class StoreAssetTypeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StoreAssetTypeSerializer

    def get_queryset(self):
        qs = StoreAssetType.objects.filter(is_active=True)
        family = self.request.query_params.get("family")
        if family:
            qs = qs.filter(family=family)
        participates = self.request.query_params.get("participates_in_planogram")
        if participates is not None:
            val = participates.lower() in ("1", "true", "yes")
            qs = qs.filter(participates_in_planogram=val)
        return qs

    @action(detail=False, methods=["get"])
    def families(self, request):
        rows = (
            StoreAssetType.objects.filter(is_active=True)
            .values_list("family")
            .order_by("family")
            .distinct()
        )
        out = []
        for (fam,) in rows:
            out.append(
                {
                    "family": fam,
                    "label": FAMILY_LABELS.get(fam, fam.replace("_", " ").title()),
                    "count": StoreAssetType.objects.filter(is_active=True, family=fam).count(),
                }
            )
        return Response(out)


class FixtureInstanceViewSet(viewsets.ModelViewSet):
    serializer_class = FixtureInstanceSerializer

    def get_queryset(self):
        qs = FixtureInstance.objects.select_related(
            "fixture_type", "store", "layout"
        ).prefetch_related("components__component_type")
        store_id = self.request.query_params.get("store")
        if store_id:
            qs = qs.filter(store_id=store_id)
        return qs

    @action(detail=False, methods=["post"], url_path="place")
    def place(self, request):
        """Place a single Fixture Instance on a store layout (minimal)."""
        store_id = request.data.get("store_id")
        fixture_type_id = request.data.get("fixture_type_id")
        layout_id = request.data.get("layout_id")
        store = get_object_or_404(Store, pk=store_id)
        ftype = get_object_or_404(FixtureType, pk=fixture_type_id)
        if layout_id:
            layout = get_object_or_404(StoreLayout, pk=layout_id, store=store)
        else:
            layout = store.layouts.filter(is_active=True).first()
            if not layout:
                layout = StoreLayout.objects.create(
                    store=store, name="Active layout", is_active=True, status="ready"
                )

        params = dict(ftype.default_params or {})
        params.update(request.data.get("params") or {})

        with transaction.atomic():
            inst = FixtureInstance.objects.create(
                store=store,
                layout=layout,
                fixture_type=ftype,
                name=request.data.get("name") or f"{ftype.code}-1",
                x_mm=int(request.data.get("x_mm", 0)),
                y_mm=int(request.data.get("y_mm", 0)),
                rotation_deg=float(request.data.get("rotation_deg", 0)),
                params=params,
                placement_mode=request.data.get("placement_mode", PlacementMode.FLOOR),
                department_id=request.data.get("department_id"),
                aisle_id=request.data.get("aisle_id"),
            )
            create_carriers_for_instance(inst)
        inst = FixtureInstance.objects.prefetch_related(
            "components__component_type"
        ).get(pk=inst.pk)
        return Response(
            FixtureInstanceSerializer(inst).data, status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=["post"], url_path="ensure-carriers")
    def ensure_carriers(self, request, pk=None):
        """Create well/shelf carriers if missing (e.g. produce bin)."""
        inst = self.get_object()
        create_carriers_for_instance(inst)
        inst = FixtureInstance.objects.prefetch_related(
            "components__component_type"
        ).get(pk=inst.pk)
        return Response(FixtureInstanceSerializer(inst).data)

    @action(detail=True, methods=["patch"], url_path="pose")
    def pose(self, request, pk=None):
        """Floor/top SoT: update Fixture Instance pose (x, y, rotation)."""
        inst = self.get_object()
        if "x_mm" in request.data:
            inst.x_mm = int(request.data["x_mm"])
        if "y_mm" in request.data:
            inst.y_mm = int(request.data["y_mm"])
        if "rotation_deg" in request.data:
            inst.rotation_deg = float(request.data["rotation_deg"])
        inst.save(update_fields=["x_mm", "y_mm", "rotation_deg", "updated_at"])
        return Response(FixtureInstanceSerializer(inst).data)

    @action(detail=False, methods=["post"], url_path="batch-bays")
    def batch_bays(self, request):
        """D1 Must: Create N bays of selected Fixture Type."""
        store = get_object_or_404(Store, pk=request.data.get("store_id"))
        ftype = get_object_or_404(FixtureType, pk=request.data.get("fixture_type_id"))
        n = int(request.data.get("bay_count", 1))
        if n < 1 or n > 50:
            return Response({"detail": "bay_count must be 1–50"}, status=400)
        layout = store.layouts.filter(is_active=True).first()
        if not layout:
            layout = StoreLayout.objects.create(
                store=store, name="Active layout", is_active=True, status="ready"
            )
        params = dict(ftype.default_params or {})
        bay_width = int(params.get("bay_width_mm", 900))
        start_x = int(request.data.get("x_mm", 0))
        y = int(request.data.get("y_mm", 0))
        aisle_id = request.data.get("aisle_id")

        with transaction.atomic():
            run = FixtureRun.objects.create(
                store=store,
                layout=layout,
                name=request.data.get("name") or f"{ftype.code} × {n}",
                bay_count=n,
            )
            created = []
            for i in range(n):
                inst = FixtureInstance.objects.create(
                    store=store,
                    layout=layout,
                    fixture_type=ftype,
                    run=run,
                    bay_index=i,
                    name=f"{ftype.code}-B{i + 1}",
                    x_mm=start_x + i * bay_width,
                    y_mm=y,
                    rotation_deg=float(request.data.get("rotation_deg", 0)),
                    params=params,
                    aisle_id=aisle_id,
                    department_id=request.data.get("department_id"),
                )
                create_carriers_for_instance(inst)
                created.append(inst)
        run = FixtureRun.objects.prefetch_related(
            "bays__components__component_type", "bays__fixture_type"
        ).get(pk=run.pk)
        return Response(FixtureRunSerializer(run).data, status=201)


class StoreAssetInstanceViewSet(viewsets.ModelViewSet):
    serializer_class = StoreAssetInstanceSerializer

    def get_queryset(self):
        qs = StoreAssetInstance.objects.select_related("asset_type", "store", "layout")
        store_id = self.request.query_params.get("store")
        if store_id:
            qs = qs.filter(store_id=store_id)
        return qs

    @action(detail=False, methods=["post"], url_path="place")
    def place(self, request):
        store = get_object_or_404(Store, pk=request.data.get("store_id"))
        atype = get_object_or_404(StoreAssetType, pk=request.data.get("asset_type_id"))
        layout = store.layouts.filter(is_active=True).first()
        if not layout:
            layout = StoreLayout.objects.create(
                store=store, name="Active layout", is_active=True, status="ready"
            )
        params = dict(atype.default_params or {})
        params.update(request.data.get("params") or {})
        modes = atype.placement_mode_options or [PlacementMode.FLOOR]
        mode = request.data.get("placement_mode") or modes[0]
        inst = StoreAssetInstance.objects.create(
            store=store,
            layout=layout,
            asset_type=atype,
            name=request.data.get("name") or atype.name,
            x_mm=int(request.data.get("x_mm", 0)),
            y_mm=int(request.data.get("y_mm", 0)),
            rotation_deg=float(request.data.get("rotation_deg", 0)),
            params=params,
            placement_mode=mode,
            source="library",
        )
        return Response(
            StoreAssetInstanceSerializer(inst).data, status=status.HTTP_201_CREATED
        )


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer

    def get_queryset(self):
        qs = Product.objects.filter(is_active=True)
        q = self.request.query_params.get("q")
        if q:
            from django.db.models import Q
            qs = qs.filter(Q(name__icontains=q) | Q(sku__icontains=q))
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category__iexact=category)
        return qs

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx

    @action(detail=False, methods=["post"], url_path="import")
    def import_csv(self, request):
        csv_file = request.FILES.get("file") or request.FILES.get("csv")
        if not csv_file:
            return Response({"detail": "CSV file required (file=)"}, status=400)
        zip_file = request.FILES.get("images") or request.FILES.get("zip")
        job = import_products_csv(csv_file, zip_file)
        return Response(
            {
                "id": job.id,
                "state": job.state,
                "created_count": job.created_count,
                "updated_count": job.updated_count,
                "error_count": job.error_count,
                "report": job.report,
            },
            status=200 if job.state == "ready" else 400,
        )

    @action(detail=True, methods=["post"], url_path="upload-image")
    def upload_image(self, request, pk=None):
        product = self.get_object()
        image = request.FILES.get("image") or request.FILES.get("file")
        if not image:
            return Response({"detail": "image file required"}, status=400)
        product.front_image = image
        product.image_incomplete = False
        product.readiness = "image_complete"
        product.save()
        return Response(ProductSerializer(product, context={"request": request}).data)


class PlanogramViewSet(viewsets.ModelViewSet):
    serializer_class = PlanogramSerializer

    def get_queryset(self):
        qs = Planogram.objects.select_related("scene", "store")
        store_id = self.request.query_params.get("store")
        if store_id:
            qs = qs.filter(store_id=store_id)
        return qs

    def perform_create(self, serializer):
        pog = serializer.save(owner=self.request.user)
        PlanogramScene.objects.get_or_create(
            planogram=pog,
            defaults={
                "graph": {"schema_version": 5, "units": "mm", "blocks": [], "placements": []}
            },
        )

    @action(detail=True, methods=["get", "put"], url_path="scene")
    def scene(self, request, pk=None):
        pog = self.get_object()
        scene, _ = PlanogramScene.objects.get_or_create(
            planogram=pog,
            defaults={
                "graph": {"schema_version": 5, "units": "mm", "blocks": [], "placements": []}
            },
        )
        if request.method == "GET":
            return Response(
                {
                    "schema_version": scene.schema_version,
                    "graph": scene.graph,
                    "updated_at": scene.updated_at,
                }
            )

        client_updated = request.data.get("updated_at")
        if client_updated:
            from django.utils.dateparse import parse_datetime

            parsed = parse_datetime(client_updated)
            if parsed and parsed < scene.updated_at:
                return Response(
                    {
                        "detail": "Conflict — reload scene",
                        "updated_at": scene.updated_at,
                    },
                    status=status.HTTP_409_CONFLICT,
                )

        graph = request.data.get("graph") or scene.graph
        # Server re-validate width-fit (A15 / C8).
        carrier_ids = set()
        for p in graph.get("placements") or []:
            ref = p.get("carrier_ref") or {}
            if ref.get("component_instance_id"):
                carrier_ids.add(ref["component_instance_id"])
        carriers = {}
        for c in ComponentInstance.objects.filter(id__in=carrier_ids):
            carriers[str(c.id)] = {
                "width_mm": c.width_mm,
                "reserved_insets_mm": c.reserved_insets_mm
                or c.component_type.reserved_inset_mm,
            }
        issues = validate_scene_width_fit(graph, carriers)
        errors = [i for i in issues if i.get("severity") == "error"]
        scene.graph = graph
        scene.schema_version = int(request.data.get("schema_version", 5))
        scene.save()
        return Response(
            {
                "schema_version": scene.schema_version,
                "graph": scene.graph,
                "updated_at": scene.updated_at,
                "validation": {"issues": issues, "ok": len(errors) == 0},
            }
        )

    @action(detail=True, methods=["post"], url_path="validate-width")
    def validate_width(self, request, pk=None):
        pog = self.get_object()
        scene = getattr(pog, "scene", None)
        graph = (request.data.get("graph") if request.data else None) or (
            scene.graph if scene else {"placements": []}
        )
        carrier_id = request.data.get("component_instance_id")
        if carrier_id:
            c = get_object_or_404(ComponentInstance, pk=carrier_id)
            plist = [
                p
                for p in (graph.get("placements") or [])
                if str((p.get("carrier_ref") or {}).get("component_instance_id"))
                == str(carrier_id)
            ]
            summary = summarize_carrier(
                c.width_mm,
                c.reserved_insets_mm or c.component_type.reserved_inset_mm,
                plist,
            )
            return Response(summary)

        carriers = {}
        for c in ComponentInstance.objects.filter(
            fixture_id__in=pog.target_fixture_ids or []
        ):
            carriers[str(c.id)] = {
                "width_mm": c.width_mm,
                "reserved_insets_mm": c.reserved_insets_mm
                or c.component_type.reserved_inset_mm,
            }
        issues = validate_scene_width_fit(graph, carriers)
        return Response({"issues": issues, "ok": not any(i["severity"] == "error" for i in issues)})

    @action(detail=True, methods=["post"], url_path="place-products")
    def place_products(self, request, pk=None):
        """
        D1 Must #4: Place user-specified SKU list on selected carrier
        using deterministic width-fit (sequential pack).
        """
        pog = self.get_object()
        scene, _ = PlanogramScene.objects.get_or_create(
            planogram=pog,
            defaults={
                "graph": {"schema_version": 5, "units": "mm", "blocks": [], "placements": []}
            },
        )
        carrier = get_object_or_404(
            ComponentInstance, pk=request.data.get("component_instance_id")
        )
        skus = request.data.get("skus") or []
        facings_default = int(request.data.get("facings", 1))
        products = list(Product.objects.filter(sku__in=skus, is_active=True))
        by_sku = {p.sku: p for p in products}
        ordered = [by_sku[s] for s in skus if s in by_sku]

        available = carrier.available_width_mm
        graph = dict(scene.graph or {})
        placements = list(graph.get("placements") or [])
        # Remove existing on this carrier if replace=true
        if request.data.get("replace", True):
            placements = [
                p
                for p in placements
                if str((p.get("carrier_ref") or {}).get("component_instance_id"))
                != str(carrier.id)
            ]

        used = sum(
            int(p.get("width_consumed_mm") or 0)
            for p in placements
            if str((p.get("carrier_ref") or {}).get("component_instance_id"))
            == str(carrier.id)
        )
        seq = 0
        placed = []
        overflow_skus = []
        for prod in ordered:
            orient = prod.orientation
            eff = prod.effective_width_mm(orient)
            facings = facings_default
            consumed = eff * facings
            if used + consumed > available:
                overflow_skus.append(prod.sku)
                continue
            entry = {
                "id": str(uuid.uuid4()),
                "product_id": prod.id,
                "sku": prod.sku,
                "carrier_ref": {
                    "fixture_instance_id": carrier.fixture_id,
                    "component_instance_id": carrier.id,
                    "kind": "shelf",
                    "face": carrier.face,
                    "index": carrier.shelf_index,
                },
                "facings": facings,
                "sequence": seq,
                "orientation": orient,
                "effective_width_mm": eff,
                "width_consumed_mm": consumed,
            }
            placements.append(entry)
            placed.append(entry)
            used += consumed
            seq += 1

        graph["placements"] = placements
        graph["schema_version"] = 5
        graph["units"] = "mm"
        graph.setdefault("blocks", [])
        scene.graph = graph
        scene.save()
        summary = summarize_carrier(
            carrier.width_mm,
            carrier.reserved_insets_mm or carrier.component_type.reserved_inset_mm,
            [
                p
                for p in placements
                if str((p.get("carrier_ref") or {}).get("component_instance_id"))
                == str(carrier.id)
            ],
        )
        return Response(
            {
                "placed": placed,
                "overflow_skus": overflow_skus,
                "summary": summary,
                "graph": scene.graph,
                "updated_at": scene.updated_at,
            }
        )


class WidthFitPreviewView(APIView):
    """Client preview helper — same formula as server validate."""

    def post(self, request):
        width_mm = int(request.data.get("carrier_width_mm", 0))
        insets = int(request.data.get("reserved_insets_mm", 0))
        placements = request.data.get("placements") or []
        # Enrich effective_width from products when only product_id given
        enriched = []
        for p in placements:
            item = dict(p)
            if "effective_width_mm" not in item and item.get("product_id"):
                prod = Product.objects.filter(pk=item["product_id"]).first()
                if prod:
                    orient = item.get("orientation") or prod.orientation
                    item["effective_width_mm"] = effective_width_mm(
                        prod.width_mm, prod.height_mm, orient
                    )
                    item.setdefault("orientation", orient)
            enriched.append(item)
        return Response(summarize_carrier(width_mm, insets, enriched))
