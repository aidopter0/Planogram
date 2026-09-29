"""Idempotent Appendix A catalog seed (org-global types)."""

from django.core.management.base import BaseCommand

from apps.catalog.models import (
    DisplayAssetType,
    FixtureComponentType,
    FixtureType,
    StoreAssetType,
)
from apps.catalog.seed_data import (
    COMPONENT_TYPES,
    DISPLAY_ASSET_TYPES,
    FIXTURE_TYPES,
    STORE_ASSET_TYPES,
)


class Command(BaseCommand):
    help = "Seed org-global Fixture / Component / Display / Store Asset types (Appendix A representative)"

    def handle(self, *args, **options):
        ft_n = ct_n = da_n = sa_n = 0
        for code, name, family, tier, params, modes in FIXTURE_TYPES:
            _, created = FixtureType.objects.update_or_create(
                code=code,
                defaults={
                    "name": name,
                    "family": family,
                    "tier": tier,
                    "default_params": params,
                    "placement_mode_options": modes,
                    "is_active": True,
                },
            )
            ft_n += int(created)
        for code, name, family, params, modes, inset in COMPONENT_TYPES:
            _, created = FixtureComponentType.objects.update_or_create(
                code=code,
                defaults={
                    "name": name,
                    "family": family,
                    "default_params": params,
                    "placement_mode_options": modes,
                    "reserved_inset_mm": inset,
                    "is_active": True,
                },
            )
            ct_n += int(created)
        for code, name, family, modes, params in DISPLAY_ASSET_TYPES:
            _, created = DisplayAssetType.objects.update_or_create(
                code=code,
                defaults={
                    "name": name,
                    "family": family,
                    "placement_mode_options": modes,
                    "default_params": params,
                    "is_active": True,
                },
            )
            da_n += int(created)
        for code, name, family, modes, participates, params in STORE_ASSET_TYPES:
            _, created = StoreAssetType.objects.update_or_create(
                code=code,
                defaults={
                    "name": name,
                    "family": family,
                    "placement_mode_options": modes,
                    "participates_in_planogram": participates,
                    "default_params": params,
                    "is_active": True,
                },
            )
            sa_n += int(created)

        self.stdout.write(
            self.style.SUCCESS(
                f"Catalog seed: fixtures +{ft_n}/{FixtureType.objects.count()}, "
                f"components +{ct_n}/{FixtureComponentType.objects.count()}, "
                f"display +{da_n}/{DisplayAssetType.objects.count()}, "
                f"store assets +{sa_n}/{StoreAssetType.objects.count()}"
            )
        )
