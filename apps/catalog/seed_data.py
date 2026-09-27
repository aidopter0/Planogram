"""Appendix A — representative typed catalog seed (org-global).

Default: representative types per family (not every SKU name as a row).
Names follow BRD Appendix A where practical. Tier = modeling/seed priority.
"""

from __future__ import annotations

from apps.catalog.models import PlacementMode as PM

FLOOR = [PM.FLOOR]
WALL = [PM.WALL, PM.FLOOR]
ATTACHED = [PM.ATTACHED, PM.SHELF]
FACE = [PM.FIXTURE_FACE, PM.FLOOR]
CEILING = [PM.CEILING]
PEG = [PM.PEGBOARD, PM.ATTACHED]


def _shelves(width=900, height=1600, depth=450, count=4, pitch=350, shelf_depth=400, faces=2):
    return {
        "bay_width_mm": width,
        "height_mm": height,
        "depth_mm": depth,
        "shelf_count": count,
        "shelf_pitch_mm": pitch,
        "shelf_depth_mm": shelf_depth,
        "faces": faces,
    }


def _solid(width, height, depth, shelf_count=0, faces=1, **extra):
    return {
        "bay_width_mm": width,
        "height_mm": height,
        "depth_mm": depth,
        "shelf_count": shelf_count,
        "faces": faces,
        **extra,
    }


# (code, name, family, tier, default_params, placement_mode_options)
FIXTURE_TYPES: list[tuple] = [
    # A — Gondola / shelving
    ("GONDOLA_DS_900", "Double-sided gondola 900 mm", "gondola", 1, _shelves(900, faces=2), FLOOR),
    ("GONDOLA_SS_900", "Single-sided wall gondola", "gondola", 1, _shelves(900, depth=400, faces=1), WALL),
    ("WALL_SHELVING", "Perimeter wall shelving", "gondola", 1, _shelves(1000, depth=350, faces=1), WALL),
    ("GONDOLA_NARROW", "Narrow gondola", "gondola", 2, _shelves(600, depth=400, faces=2), FLOOR),
    ("GONDOLA_WIDE_1200", "Wide gondola 1200 mm", "gondola", 1, _shelves(1200, faces=2), FLOOR),
    ("GONDOLA_LOW", "Low-height gondola", "gondola", 2, _shelves(900, height=1200, count=3, faces=2), FLOOR),
    ("GONDOLA_HIGH", "High gondola", "gondola", 2, _shelves(900, height=2100, count=5, pitch=320, faces=2), FLOOR),
    ("GONDOLA_ENDCAP", "End-cap gondola", "gondola", 1, _shelves(900, depth=600, faces=1), FLOOR),
    ("GONDOLA_PROMO", "Promotional gondola", "gondola", 2, _shelves(900, count=3, faces=1), FLOOR),
    # keep legacy code used by earlier seed/demo planograms
    ("GONDOLA_900", "Standard Gondola 900 mm", "gondola", 1, _shelves(900, faces=2), FLOOR),
    # E — Produce
    ("PRODUCE_TABLE", "Produce table", "produce", 1, _solid(1800, 850, 900), FLOOR),
    ("PRODUCE_ISLAND", "Produce island", "produce", 1, _solid(2400, 900, 1200), FLOOR),
    ("PRODUCE_TIERED", "Tiered produce rack", "produce", 1, _solid(1200, 1600, 700, shelf_count=3, shelf_pitch_mm=280), FLOOR),
    ("PRODUCE_SLOPED", "Sloped produce rack", "produce", 2, _solid(1200, 1400, 800, shelf_count=3), FLOOR),
    ("PRODUCE_BIN", "Produce bin", "produce", 1, _solid(800, 700, 600), FLOOR),
    ("PRODUCE_WOOD_TABLE", "Wooden produce table", "produce", 2, _solid(1600, 850, 900), FLOOR),
    ("PRODUCE_WALL", "Produce wall", "produce", 2, _solid(2000, 1800, 500, shelf_count=4, faces=1), WALL),
    # F — Chilled
    ("CHILLER_MULTIDECK", "Open multideck chiller", "chilled", 1, _shelves(1250, 2000, 900, 5, 300, 500, faces=1), FLOOR),
    ("CHILLER_VERTICAL", "Vertical chiller", "chilled", 1, _shelves(900, 2000, 800, 5, 300, 450, faces=1), FLOOR),
    ("CHILLER_ISLAND", "Island chiller", "chilled", 1, _solid(2000, 900, 1200, shelf_count=2), FLOOR),
    ("CHILLER_GLASS_DOOR", "Glass-door chiller", "chilled", 1, _shelves(1250, 2000, 750, 5, 300, 500, faces=1), FLOOR),
    ("CHILLER_DAIRY", "Dairy chiller", "chilled", 1, _shelves(1250, 2000, 850, 5, 300, 500, faces=1), FLOOR),
    ("CHILLER_SERVE_OVER", "Serve-over counter", "chilled", 1, _solid(2500, 1200, 1000), FLOOR),
    ("CHILLER_DELI_CASE", "Deli display case", "chilled", 1, _solid(2000, 1300, 900), FLOOR),
    # G — Frozen
    ("FREEZER_ISLAND", "Island freezer", "frozen", 1, _solid(2000, 850, 1000), FLOOR),
    ("FREEZER_CHEST", "Chest freezer", "frozen", 1, _solid(1500, 900, 700), FLOOR),
    ("FREEZER_OPEN_TOP", "Open-top freezer", "frozen", 2, _solid(1800, 850, 900), FLOOR),
    ("FREEZER_UPRIGHT", "Upright glass-door freezer", "frozen", 1, _shelves(1250, 2000, 750, 5, 300, 500, faces=1), FLOOR),
    ("FREEZER_MULTI_DOOR", "Multi-door freezer", "frozen", 1, _shelves(2500, 2000, 750, 5, 300, 500, faces=1), FLOOR),
    # H — Bakery
    ("BAKERY_BREAD_RACK", "Bread rack", "bakery", 1, _shelves(900, 1800, 500, 5, 300, 400, faces=1), FLOOR),
    ("BAKERY_GONDOLA", "Bakery gondola", "bakery", 1, _shelves(900, 1600, 450, 4, faces=2), FLOOR),
    ("BAKERY_TABLE", "Bakery table", "bakery", 1, _solid(1600, 900, 800), FLOOR),
    ("BAKERY_GLASS_CASE", "Glass bakery case", "bakery", 1, _solid(1500, 1400, 700), FLOOR),
    ("BAKERY_PASTRY", "Pastry display", "bakery", 2, _solid(1200, 1400, 700), FLOOR),
    # I — Meat / fish / deli
    ("DELI_COUNTER", "Meat / Deli counter", "deli", 1, _solid(3000, 1200, 1000), FLOOR),
    ("SEAFOOD_ICEBED", "Seafood ice-bed display", "deli", 1, _solid(2500, 1100, 1000), FLOOR),
    ("CHEESE_COUNTER", "Cheese counter", "deli", 2, _solid(2000, 1200, 900), FLOOR),
    ("HOT_FOOD_COUNTER", "Hot food counter", "deli", 2, _solid(2000, 1200, 900), FLOOR),
    # J — Bulk / specialty
    ("BULK_BIN", "Bulk bin", "bulk", 1, _solid(600, 1400, 500), FLOOR),
    ("BULK_GRAVITY", "Gravity bin", "bulk", 1, _solid(400, 1600, 400), FLOOR),
    ("WINE_RACK", "Wine rack / display", "bulk", 1, _shelves(900, 2000, 400, 6, 280, 350, faces=1), FLOOR),
    ("BEVERAGE_DISPLAY", "Beverage / water display", "bulk", 2, _shelves(1000, 1600, 500, 4, faces=1), FLOOR),
    ("SEASONAL_DISPLAY", "Seasonal display", "bulk", 3, _solid(1200, 1600, 800), FLOOR),
    # K — Checkout
    ("CHECKOUT_COUNTER", "Checkout counter", "checkout", 1, _solid(2800, 1000, 900), FLOOR),
    ("CHECKOUT_SELF", "Self-checkout", "checkout", 1, _solid(900, 1400, 800), FLOOR),
    ("BAGGING_STATION", "Bagging station", "checkout", 1, _solid(1200, 1000, 700), FLOOR),
    ("IMPULSE_RACK", "Impulse rack", "checkout", 1, _shelves(600, 1400, 350, 4, 250, 300, faces=1), FLOOR),
    ("CHECKOUT_GRABGO", "Grab-and-go refrigerator", "checkout", 2, _shelves(900, 1800, 700, 4, faces=1), FLOOR),
]

COMPONENT_TYPES: list[tuple] = [
    ("SHELF_STD", "Standard shelf/board", "shelf", {}, ATTACHED, 0),
    ("SHELF_BASE", "Base shelf", "shelf", {"depth_mm": 450}, ATTACHED, 0),
    ("SHELF_TOP", "Top shelf", "shelf", {}, ATTACHED, 0),
    ("DIVIDER", "Shelf divider", "divider", {}, [PM.SHELF], 10),
    ("DIVIDER_ACRYLIC", "Acrylic divider", "divider", {}, [PM.SHELF], 8),
    ("DIVIDER_WIRE", "Wire divider", "divider", {}, [PM.SHELF], 6),
    ("PUSHER", "Product pusher", "shelf", {}, [PM.SHELF], 0),
    ("PRICE_RAIL", "Price rail", "rail", {}, ATTACHED, 0),
    ("ESL_RAIL", "Electronic shelf-label rail", "rail", {}, ATTACHED, 0),
    ("BACK_PANEL", "Back panel", "panel", {}, ATTACHED, 0),
    ("SIDE_PANEL", "Side panel", "panel", {}, ATTACHED, 0),
    ("PEGBOARD", "Pegboard", "hanging", {}, PEG, 0),
    ("SLATWALL", "Slatwall", "hanging", {}, PEG, 0),
    ("HOOK", "Hook", "hanging", {}, PEG, 0),
    ("PEG_HOOK", "Peg hook", "hanging", {}, PEG, 0),
    ("WIRE_BASKET", "Wire basket", "basket", {}, ATTACHED, 0),
    ("BIN", "Bin", "basket", {}, ATTACHED, 0),
]

DISPLAY_ASSET_TYPES: list[tuple] = [
    ("ENDCAP", "Endcap", "endcap", FACE, _solid(900, 1600, 600)),
    ("ENDCAP_HALF", "Half-endcap", "endcap", FACE, _solid(900, 1200, 400)),
    ("ENDCAP_FULL", "Full-height endcap", "endcap", FACE, _solid(900, 2000, 600)),
    ("PROMO_TOWER", "Promotional tower", "promo", FLOOR, _solid(600, 1800, 600)),
    ("DUMP_BIN", "Dump bin", "bin", FLOOR, _solid(800, 900, 800)),
    ("FLOOR_BIN", "Floor bin", "bin", FLOOR, _solid(700, 800, 700)),
    ("PALLET_DISPLAY", "Pallet display", "pallet", FLOOR, _solid(1200, 1400, 1000)),
    ("HALF_PALLET", "Half-pallet display", "pallet", FLOOR, _solid(800, 1200, 600)),
    ("FSDU", "FSDU / free-standing display unit", "fsdu", FLOOR, _solid(600, 1600, 500)),
    ("PROMO_TABLE", "Promotional table", "promo", FLOOR, _solid(1200, 900, 800)),
    ("POWER_WING", "Power wing / side-wing", "hanging", FACE, _solid(400, 1400, 300)),
    ("CLIP_STRIP", "Clip strip", "hanging", FACE, _solid(80, 1200, 40)),
    ("COUNTERTOP_DISPLAY", "Countertop display", "promo", [PM.SHELF, PM.FLOOR], _solid(400, 500, 300)),
]

# (code, name, family, placement_modes, participates_in_planogram, default_params)
STORE_ASSET_TYPES: list[tuple] = [
    ("COLUMN", "Structural column", "structure", FLOOR, False, _solid(400, 3000, 400)),
    ("PILLAR", "Pillar", "structure", FLOOR, False, _solid(500, 3000, 500)),
    ("WALL_SEGMENT", "Wall segment", "structure", WALL, False, _solid(3000, 3000, 150)),
    ("DOOR", "Door", "opening", WALL, False, _solid(1000, 2100, 100)),
    ("WINDOW", "Window", "opening", WALL, False, _solid(1500, 1200, 100)),
    ("ENTRANCE_PORTAL", "Entrance portal", "opening", FLOOR, False, _solid(2400, 2800, 400)),
    ("FIRE_EXIT", "Fire exit", "opening", WALL, False, _solid(1000, 2100, 100)),
    ("ESCALATOR", "Escalator", "vertical", FLOOR, False, _solid(1500, 0, 4000)),
    ("STAIRS", "Stairs", "vertical", FLOOR, False, _solid(1400, 0, 3500)),
    ("ELEVATOR", "Elevator", "vertical", FLOOR, False, _solid(2000, 2800, 2000)),
    ("TROLLEY_BAY", "Trolley bay", "service", FLOOR, False, _solid(2000, 1200, 1500)),
    ("BASKET_STAND", "Basket stand", "service", FLOOR, True, _solid(800, 1200, 600)),
    ("WASTE_BIN", "Waste bin", "service", FLOOR, False, _solid(500, 900, 500)),
    ("CATEGORY_SIGN", "Category / hanging sign", "signage", CEILING, False, _solid(1200, 400, 80)),
    ("PROMO_SIGN", "Promotional hanging sign", "signage", CEILING, False, _solid(1500, 500, 80)),
    ("DIGITAL_SCREEN", "Digital screen", "signage", WALL, False, _solid(1200, 700, 100)),
    ("LIGHTBOX", "Lightbox", "signage", WALL, False, _solid(1500, 600, 120)),
    ("CEILING_SIGN", "Ceiling sign", "signage", CEILING, False, _solid(2000, 400, 80)),
]

FAMILY_LABELS = {
    "gondola": "Gondola / shelving",
    "produce": "Produce",
    "chilled": "Chilled / refrigerated",
    "frozen": "Frozen",
    "bakery": "Bakery",
    "deli": "Meat / fish / deli",
    "bulk": "Bulk / specialty",
    "checkout": "Checkout & impulse",
    "shelf": "Shelves",
    "divider": "Dividers",
    "rail": "Rails",
    "panel": "Panels",
    "hanging": "Hanging / peg",
    "basket": "Baskets & bins",
    "endcap": "Endcaps",
    "promo": "Promotional",
    "bin": "Bins",
    "pallet": "Pallet displays",
    "fsdu": "FSDU",
    "structure": "Structure",
    "opening": "Openings",
    "vertical": "Vertical circulation",
    "service": "Service",
    "signage": "Signage",
}
