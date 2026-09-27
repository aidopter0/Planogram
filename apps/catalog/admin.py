from django.contrib import admin

from apps.catalog.models import (
    DisplayAssetType,
    FixtureComponentType,
    FixtureType,
    StoreAssetType,
)
from apps.fixtures.models import ComponentInstance, FixtureInstance, FixtureRun
from apps.layouts.models import IngestJob, StoreLayout
from apps.planograms.models import Planogram, PlanogramScene
from apps.products.models import Product, ProductImportJob
from apps.stores.models import Aisle, Department, Store

admin.site.register(Store)
admin.site.register(Department)
admin.site.register(Aisle)
admin.site.register(StoreLayout)
admin.site.register(IngestJob)
admin.site.register(FixtureType)
admin.site.register(FixtureComponentType)
admin.site.register(DisplayAssetType)
admin.site.register(StoreAssetType)
admin.site.register(FixtureRun)
admin.site.register(FixtureInstance)
admin.site.register(ComponentInstance)
admin.site.register(Product)
admin.site.register(ProductImportJob)
admin.site.register(Planogram)
admin.site.register(PlanogramScene)
