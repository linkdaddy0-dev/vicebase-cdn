import os
import json
from PIL import Image, ImageDraw, ImageFont

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else r"c:\Users\rosha\Documents\vicebase-cdn\scripts"
CDN_DIR = os.path.dirname(SCRIPTS_DIR)
MEDIA_DIR = os.path.join(CDN_DIR, 'media')

NEW_ASSETS = [
    # type, name, folder
    ("character", "character_lucia_retro_dress", "characters/lucia_retro_dress", "Lucia (Retro Dress)"),
    ("character", "character_jason_retro_suit", "characters/jason_retro_suit", "Jason (Retro Suit)"),
    ("character", "character_lucia_macca_gear", "characters/lucia_macca_gear", "Lucia (Macca Gear)"),
    ("character", "character_jason_macca_gear", "characters/jason_macca_gear", "Jason (Macca Gear)"),
    ("character", "character_cal_hampton", "characters/cal_hampton", "Cal Hampton"),
    ("character", "character_boobie_ike", "characters/boobie_ike", "Boobie Ike"),
    ("character", "character_raul_bautista", "characters/raul_bautista", "Raul Bautista"),
    ("character", "character_brian_heder", "characters/brian_heder", "Brian Heder"),
    ("character", "character_real_dimez", "characters/real_dimez", "Real Dimez"),
    ("character", "character_drequan_priest", "characters/drequan_priest", "Dre'Quan Priest"),
    
    ("vehicle", "vehicle_stanier_55", "vehicles/stanier_55", "'55 Vapid Stanier"),
    ("vehicle", "vehicle_dominator_buggy", "vehicles/dominator_buggy", "'67 Vapid Dominator Buggy"),
    ("vehicle", "vehicle_shitzu_squalo", "vehicles/shitzu_squalo", "Shitzu Squalo"),
    ("vehicle", "vehicle_dinka_enduro", "vehicles/dinka_enduro", "Dinka Enduro"),
    ("vehicle", "vehicle_ganado_retro", "vehicles/ganado_retro", "Vapid Ganado Retro Build"),
    ("vehicle", "vehicle_crest_kayak", "vehicles/crest_kayak", "Crest Kayak"),
    ("vehicle", "vehicle_cheetah_95", "vehicles/cheetah_95", "'95 Grotti Cheetah"),
    
    ("weapon", "weapon_revolver_morgan", "weapons/revolver_morgan", "Hawk & Little Morgan Revolver"),
    ("weapon", "weapon_skin_tropical", "weapons/skin_tropical", "Tropical Weapon Skin"),
    
    ("location", "location_ambrosia", "locations/ambrosia", "Ambrosia"),
    ("location", "location_port_gellhorn", "locations/port_gellhorn", "Port Gellhorn"),
    ("location", "location_kalaga", "locations/kalaga", "Mount Kalaga"),
    ("location", "location_leonida_keys", "locations/leonida_keys", "Leonida Keys"),
    ("location", "location_grassrivers", "locations/grassrivers", "Grassrivers")
]

def create_gradient_image(width, height, text_title):
    # Create gradient: deep purple (30, 10, 50) to neon sunset pink/orange (230, 60, 120)
    image = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(image)
    
    for y in range(height):
        # Interpolate colors
        r = int(30 + (200 * y / height))
        g = int(10 + (50 * y / height))
        b = int(50 + (70 * y / height))
        draw.line([(0, y), (width, y)], fill=(r, g, b))
        
    # Draw simple textual indicator centered
    # We use a default fallback font if TTF is not available
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
        
    # Draw text in the middle
    text_color = (255, 255, 255)
    draw.text((width // 10, height // 2), text_title, fill=text_color)
    
    return image

def main():
    print(f"Generating {len(NEW_ASSETS)} media folder placeholders...")
    for type_name, asset_id, rel_path, display_name in NEW_ASSETS:
        folder_path = os.path.join(MEDIA_DIR, rel_path)
        os.makedirs(folder_path, exist_ok=True)
        
        # 1. card.webp (800x450)
        card_img = create_gradient_image(800, 450, display_name)
        card_img.save(os.path.join(folder_path, "card.webp"), "WEBP", quality=85)
        
        # 2. thumb.webp (150x150)
        thumb_img = create_gradient_image(150, 150, display_name[:15])
        thumb_img.save(os.path.join(folder_path, "thumb.webp"), "WEBP", quality=85)
        
        # 3. hero.webp (1920x1080)
        hero_img = create_gradient_image(1920, 1080, display_name)
        hero_img.save(os.path.join(folder_path, "hero.webp"), "WEBP", quality=85)
        
        # 4. metadata.json
        metadata = {
            "id": asset_id,
            "name": display_name,
            "thumbnail": "thumb.webp",
            "card": "card.webp",
            "hero": "hero.webp",
            "gallery": []
        }
        with open(os.path.join(folder_path, "metadata.json"), "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
            
        print(f"  Generated media files for {asset_id} in {rel_path}")

if __name__ == "__main__":
    main()
