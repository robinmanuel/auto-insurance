# =========================================================
# DAMAGE ↔ PART RULES
# =========================================================

PART_DAMAGE_MAP = {

    # HEADLIGHTS
    "headlight": ["broken_lamp", "crack", "scratch"],
    "left_headlight": ["broken_lamp", "crack", "scratch"],
    "right_headlight": ["broken_lamp", "crack", "scratch"],

    # TAIL LIGHTS
    "tail-light": ["broken_lamp", "crack", "scratch"],
    "left_tail-light": ["broken_lamp", "crack", "scratch"],
    "right_tail-light": ["broken_lamp", "crack", "scratch"],

    # FENDERS
    "fender": ["dent", "scratch", "crack"],
    "left_fender": ["dent", "scratch", "crack"],
    "right_fender": ["dent", "scratch", "crack"],

    # HOOD
    "hood": ["dent", "scratch"],

    # DOORS
    "front-door": ["dent", "scratch"],
    "back-door": ["dent", "scratch"],

    "left_front-door": ["dent", "scratch"],
    "right_front-door": ["dent", "scratch"],

    "left_back-door": ["dent", "scratch"],
    "right_back-door": ["dent", "scratch"],

    # BUMPERS
    "front-bumper": ["dent", "scratch", "crack"],
    "back-bumper": ["dent", "scratch", "crack"],

    # GLASS
    "windshield": ["shattered_glass", "crack"],
    "back-windshield": ["shattered_glass", "crack"],

    "front-window": ["shattered_glass", "crack"],
    "back-window": ["shattered_glass", "crack"],

    "left_front-window": ["shattered_glass", "crack"],
    "right_front-window": ["shattered_glass", "crack"],

    "left_back-window": ["shattered_glass", "crack"],
    "right_back-window": ["shattered_glass", "crack"],

    # WHEELS
    "front-wheel": ["flat_tire"],
    "back-wheel": ["flat_tire"],

    "left_front-wheel": ["flat_tire"],
    "right_front-wheel": ["flat_tire"],

    "left_back-wheel": ["flat_tire"],
    "right_back-wheel": ["flat_tire"],

    # OTHER PANELS
    "quarter-panel": ["dent", "scratch"],
    "rocker-panel": ["dent", "scratch"],
    "roof": ["dent", "scratch"],
    "trunk": ["dent", "scratch"],

    # MIRRORS
    "mirror": ["crack", "scratch", "broken_lamp"],
    "left_mirror": ["crack", "scratch", "broken_lamp"],
    "right_mirror": ["crack", "scratch", "broken_lamp"],

    # GRILLE
    "grille": ["crack", "scratch"]
}


def is_damage_valid_for_part(part_name, damage_type):

    part_name = str(part_name).lower()
    damage_type = str(damage_type).lower()

    allowed = PART_DAMAGE_MAP.get(part_name, [])

    return damage_type in allowed