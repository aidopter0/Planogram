from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.api import views

router = DefaultRouter()
router.register(r"stores", views.StoreViewSet)
router.register(r"departments", views.DepartmentViewSet)
router.register(r"aisles", views.AisleViewSet)
router.register(r"catalog/fixture-types", views.FixtureTypeViewSet, basename="fixture-types")
router.register(
    r"catalog/component-types",
    views.FixtureComponentTypeViewSet,
    basename="component-types",
)
router.register(
    r"catalog/display-asset-types",
    views.DisplayAssetTypeViewSet,
    basename="display-asset-types",
)
router.register(
    r"catalog/store-asset-types",
    views.StoreAssetTypeViewSet,
    basename="store-asset-types",
)
router.register(r"fixtures", views.FixtureInstanceViewSet, basename="fixtures")
router.register(r"store-assets", views.StoreAssetInstanceViewSet, basename="store-assets")
router.register(r"products", views.ProductViewSet, basename="products")
router.register(r"planograms", views.PlanogramViewSet, basename="planograms")

urlpatterns = [
    path("healthz/", views.healthz),
    path("width-fit/preview/", views.WidthFitPreviewView.as_view()),
    path("", include(router.urls)),
]
