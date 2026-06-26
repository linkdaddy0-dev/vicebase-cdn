import os
import subprocess
import json
import shutil
from PIL import Image
import cv2

# Define directory structures
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
CDN_DIR = os.path.dirname(SCRIPTS_DIR)
MEDIA_DIR = os.path.join(CDN_DIR, 'media')
CONTENT_DIR = os.path.join(CDN_DIR, 'content')
APP_ASSETS_DIR = r"C:\Users\rosha\Documents\GTA6 App\app\src\main\assets\data"

# Video URL and target timestamps (in seconds)
VIDEO_URL = "https://www.youtube.com/watch?v=QdBZY2fkU-0"
VIDEO_ID = "QdBZY2fkU-0"

TARGETS = {
    "character_lucia": {
        "time": 8.0,
        "folder": os.path.join(MEDIA_DIR, 'characters', 'lucia'),
        "type": "character",
        "json_path": os.path.join(CONTENT_DIR, 'characters', 'characters.json'),
        "id": "character_lucia"
    },
    "character_jason": {
        "time": 81.0,
        "folder": os.path.join(MEDIA_DIR, 'characters', 'jason'),
        "type": "character",
        "json_path": os.path.join(CONTENT_DIR, 'characters', 'characters.json'),
        "id": "character_jason"
    },
    "vehicle_cheetah": {
        "time": 33.0,
        "folder": os.path.join(MEDIA_DIR, 'vehicles', 'cheetah'),
        "type": "vehicle",
        "json_path": os.path.join(CONTENT_DIR, 'vehicles', 'vehicles.json'),
        "id": "vehicle_cheetah"
    },
    "weapon_pistol": {
        "time": 77.0,
        "folder": os.path.join(MEDIA_DIR, 'weapons', 'pistol'),
        "type": "weapon",
        "json_path": os.path.join(CONTENT_DIR, 'weapons', 'weapons.json'),
        "id": "weapon_pistol"
    },
    "location_leonida": {
        "time": 12.0,
        "folder": os.path.join(MEDIA_DIR, 'locations', 'leonida'),
        "type": "location",
        "json_path": os.path.join(CONTENT_DIR, 'locations', 'locations.json'),
        "id": "location_leonida"
    },
    "location_vice_city": {
        "time": 5.0,
        "folder": os.path.join(MEDIA_DIR, 'locations', 'vice_city'),
        "type": "location",
        "json_path": os.path.join(CONTENT_DIR, 'locations', 'locations.json'),
        "id": "location_vice_city"
    }
}

def download_video(video_url, output_path):
    print("Downloading low-resolution official GTA VI Trailer 1 from YouTube...")
    try:
        # Try downloading the worst format to save time and bandwidth
        subprocess.run(["yt-dlp", "-f", "worst[ext=mp4]/worst", video_url, "-o", output_path], check=True)
        print("Video download completed successfully.")
        return True
    except Exception as e:
        print(f"Error during video download: {e}")
        # Secondary fallback if specific formats fail
        try:
            print("Retrying download with default worst format...")
            subprocess.run(["yt-dlp", "-f", "worst", video_url, "-o", output_path], check=True)
            return True
        except Exception as e2:
            print(f"Fallback download failed: {e2}")
            return False

def extract_frames(video_path):
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return False
        
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0:
        fps = 30.0
    print(f"Loaded video. FPS: {fps}")

    for name, target in TARGETS.items():
        print(f"\nProcessing {name}...")
        frame_number = int(target['time'] * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()
        
        if not ret:
            print(f"Failed to read frame at {target['time']}s. Trying safe fallback...")
            cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, frame_number - 15))
            ret, frame = cap.read()
            
        if ret:
            os.makedirs(target['folder'], exist_ok=True)
            
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb_frame)
            
            # 1. hero.webp
            hero_path = os.path.join(target['folder'], 'hero.webp')
            img.save(hero_path, 'WEBP', quality=85)
            print(f"Saved hero: {hero_path}")
            
            # 2. card.webp (800x450 landscape)
            card_path = os.path.join(target['folder'], 'card.webp')
            card = img.resize((800, 450), Image.Resampling.LANCZOS)
            card.save(card_path, 'WEBP', quality=85)
            print(f"Saved card: {card_path}")
            
            # 3. thumb.webp (150x150 square)
            w, h = img.size
            min_dim = min(w, h)
            left = (w - min_dim) / 2
            top = (h - min_dim) / 2
            right = (w + min_dim) / 2
            bottom = (h + min_dim) / 2
            thumb = img.crop((left, top, right, bottom)).resize((150, 150), Image.Resampling.LANCZOS)
            thumb_path = os.path.join(target['folder'], 'thumb.webp')
            thumb.save(thumb_path, 'WEBP', quality=85)
            print(f"Saved thumbnail: {thumb_path}")
            
            # Save metadata.json
            metadata = {
                "id": target['id'],
                "name": os.path.basename(target['folder']).replace('_', ' ').title(),
                "thumbnail": "thumb.webp",
                "card": "card.webp",
                "hero": "hero.webp",
                "gallery": []
            }
            with open(os.path.join(target['folder'], 'metadata.json'), 'w') as f:
                json.dump(metadata, f, indent=2)
        else:
            print(f"Error: Could not extract frame for {name}")
            
    cap.release()
    return True

def update_dataset_json(target_id, json_path, card_url, video_url):
    if not os.path.exists(json_path):
        print(f"JSON path not found: {json_path}")
        return
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    updated = False
    for item in data.get('items', []):
        if item.get('id') == target_id:
            item['imageUrl'] = card_url
            item['videoUrl'] = video_url
            updated = True
            break
            
    if updated:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Updated {os.path.basename(json_path)} for ID {target_id}")
    else:
        print(f"Warning: ID {target_id} not found in {json_path}")

def update_assets_manifest():
    manifest_path = os.path.join(MEDIA_DIR, 'assets.json')
    assets = []
    # Walk the media directory and find metadata.json files
    for root, dirs, files in os.walk(MEDIA_DIR):
        if 'metadata.json' in files:
            meta_path = os.path.join(root, 'metadata.json')
            try:
                with open(meta_path, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                
                rel_folder = os.path.relpath(root, CDN_DIR).replace('\\', '/')
                parent_folder = os.path.basename(os.path.dirname(root))
                asset_type = parent_folder.rstrip('s')
                
                assets.append({
                    "id": meta['id'],
                    "type": asset_type,
                    "path": rel_folder,
                    "thumbnail": f"{rel_folder}/thumb.webp",
                    "card": f"{rel_folder}/card.webp",
                    "hero": f"{rel_folder}/hero.webp",
                    "gallery": meta.get('gallery', [])
                })
            except Exception as e:
                print(f"Error reading metadata at {meta_path}: {e}")
                
    manifest = {"assets": assets}
    manifest["assets"].sort(key=lambda x: x["id"])
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    print("Updated media/assets.json dynamically from metadata.json files.")

def sync_to_app_assets():
    print("\nSyncing updated datasets to Android app assets...")
    os.makedirs(APP_ASSETS_DIR, exist_ok=True)
    for dataset_name in ["characters", "vehicles", "weapons", "locations", "timeline", "news"]:
        src = os.path.join(CONTENT_DIR, dataset_name, f"{dataset_name}.json")
        dst = os.path.join(APP_ASSETS_DIR, f"{dataset_name}.json")
        if os.path.exists(src):
            shutil.copy(src, dst)
            print(f"Synchronized {dataset_name}.json to app assets folder.")

def main():
    video_file = os.path.join(SCRIPTS_DIR, "temp_trailer.mp4")
    
    # 1. Download trailer video
    download_success = download_video(VIDEO_URL, video_file)
    if not download_success:
        print("Failed to download trailer. Exiting pipeline.")
        return

    # 2. Extract frames and process media
    extract_success = extract_frames(video_file)
    if not extract_success:
        print("Failed to process video frames. Exiting pipeline.")
        return

    # 3. Clean up video file
    if os.path.exists(video_file):
        os.remove(video_file)
        print("Cleaned up temporary trailer video file.")

    # 4. Update assets.json
    update_assets_manifest()

    # 5. Update JSON files with CDN links
    print("\nUpdating dataset JSON files with CDN URLs...")
    for name, target in TARGETS.items():
        card_url = f"https://cdn.jsdelivr.net/gh/linkdaddy0-dev/vicebase-cdn@main/media/{target['type']}s/{os.path.basename(target['folder'])}/card.webp"
        video_url = f"https://www.youtube.com/watch?v={VIDEO_ID}"
        update_dataset_json(target['id'], target['json_path'], card_url, video_url)

    # 6. Run CDN validation and build manifest/search indexes
    print("\nRunning CDN build and validation script...")
    try:
        subprocess.run(["node", os.path.join(SCRIPTS_DIR, "validate.js")], check=True)
        print("Validation and build completed successfully.")
    except Exception as e:
        print(f"Error running validate.js: {e}")

    # 7. Sync updated datasets to Android assets
    sync_to_app_assets()
    
    print("\nAll pipeline tasks successfully completed!")

if __name__ == "__main__":
    main()
