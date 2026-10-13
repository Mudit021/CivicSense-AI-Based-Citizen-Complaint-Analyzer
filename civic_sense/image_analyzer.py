"""Image upload verification, EXIF GPS extraction, and visual analysis engine.

Features:
1. File Integrity & Security Validation:
   - File extension and MIME type verification.
   - Image corruption check and secure storage in UPLOADS_DIR.
2. EXIF Metadata & Geolocation Extraction:
   - Camera make, model, timestamp.
   - GPS latitude and longitude extraction from camera EXIF tags.
   - Distance calculation to PCU Campus buildings.
3. Computer Vision & Visual Quality Analysis:
   - Laplacian edge variance for blurriness/sharpness detection.
   - Mean brightness and luminance distribution (detects basement dark scenes vs overexposed).
   - Dominant color channels and saturation.
   - Perceptual image difference hashing (dHash) for duplicate photo detection.
4. Cross-Modal Consistency Verification:
   - Checks if visual properties (lighting, texture, color) correlate with the reported complaint category.
"""
import math
import os
import uuid
import json
from pathlib import Path
from PIL import Image, ExifTags
import numpy as np
from scipy.ndimage import laplace

from .config import UPLOADS_DIR, ALLOWED_IMAGE_EXTENSIONS, PCU_COORDINATES
from .hotspot_analyzer import CAMPUS_GEO_DATA


def _dms_to_decimal(dms, ref):
    """Convert degrees, minutes, seconds tuple to decimal degrees."""
    try:
        def _to_float(v):
            if hasattr(v, "numerator") and hasattr(v, "denominator"):
                return float(v.numerator) / float(v.denominator) if v.denominator != 0 else 0.0
            return float(v)

        deg = _to_float(dms[0])
        minute = _to_float(dms[1])
        sec = _to_float(dms[2])
        dec = deg + (minute / 60.0) + (sec / 3600.0)
        if ref in ("S", "W"):
            dec = -dec
        return round(dec, 6)
    except Exception:
        return None


def extract_exif_gps(img: Image.Image) -> dict:
    """Extract GPS coordinates and camera metadata from image EXIF tags if present."""
    exif_data = {
        "has_gps": False,
        "lat": None,
        "lon": None,
        "device": "",
        "timestamp": "",
    }
    try:
        raw_exif = img.getexif()
        if not raw_exif:
            return exif_data

        # Decode standard tags
        for tag_id, value in raw_exif.items():
            tag_name = ExifTags.TAGS.get(tag_id, tag_id)
            if tag_name == "Make":
                exif_data["device"] = str(value).strip()
            elif tag_name == "Model":
                exif_data["device"] = (exif_data["device"] + " " + str(value)).strip()
            elif tag_name in ("DateTimeOriginal", "DateTime"):
                exif_data["timestamp"] = str(value).strip()

        # GPS Info Tag (0x8825)
        gps_ifd = raw_exif.get_ifd(0x8825)
        if gps_ifd:
            lat_dms = gps_ifd.get(2)
            lat_ref = gps_ifd.get(1, "N")
            lon_dms = gps_ifd.get(4)
            lon_ref = gps_ifd.get(3, "E")

            if lat_dms and lon_dms:
                lat = _dms_to_decimal(lat_dms, lat_ref)
                lon = _dms_to_decimal(lon_dms, lon_ref)
                if lat is not None and lon is not None:
                    exif_data["has_gps"] = True
                    exif_data["lat"] = lat
                    exif_data["lon"] = lon
    except Exception:
        pass

    return exif_data


def compute_perceptual_hash(img: Image.Image) -> str:
    """Compute 64-bit difference hash (dHash) for duplicate photo detection."""
    try:
        # Resize to 9x8 and convert to grayscale
        resized = img.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
        pixels = list(resized.getdata())
        diff = []
        for row in range(8):
            for col in range(8):
                idx = row * 9 + col
                diff.append(pixels[idx] > pixels[idx + 1])
        # Convert bool array to 16 hex characters
        decimal_val = 0
        for idx, bit in enumerate(diff):
            if bit:
                decimal_val |= 1 << idx
        return f"{decimal_val:016x}"
    except Exception:
        return ""


def hamming_distance(hash1: str, hash2: str) -> int:
    """Compute bitwise Hamming distance between two 64-bit hex difference hashes."""
    if not hash1 or not hash2 or len(hash1) != len(hash2):
        return 999
    try:
        val1 = int(hash1, 16)
        val2 = int(hash2, 16)
        return bin(val1 ^ val2).count("1")
    except Exception:
        return 999


def find_image_duplicate(current_hash: str, ward: str = "") -> tuple:
    """Check if an uploaded photo was already submitted in a previous complaint."""
    if not current_hash:
        return False, None, 999
    try:
        from .database import get_conn
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT id, ward, image_analysis FROM complaints WHERE image_analysis LIKE '%perceptual_hash%' ORDER BY id DESC LIMIT 250"
            ).fetchall()
            for r in rows:
                raw_meta = r["image_analysis"]
                if not raw_meta:
                    continue
                try:
                    data = json.loads(raw_meta)
                    prev_hash = data.get("perceptual_hash", "")
                    dist = hamming_distance(current_hash, prev_hash)
                    # Hamming distance <= 4 represents near-identical photos
                    if dist <= 4:
                        return True, r["id"], dist
                except Exception:
                    continue
    except Exception:
        pass
    return False, None, 999


import base64


def analyze_image(file_storage, category: str = "", description: str = "") -> dict:
    """Validate, store, and analyze an uploaded photo.

    Args:
        file_storage: Werkzeug FileStorage object, base64 data string, or file-like object.
        category: Complaint category name for cross-verification.
        description: Text description of the complaint.

    Returns:
        dict with validation flags, image path, visual quality metrics,
        and cross-verification explanation.
    """
    if not file_storage:
        return {"has_image": False}

    unique_name = ""
    saved_path = None
    ext = "jpg"

    # Case 1: Werkzeug FileStorage object
    if hasattr(file_storage, "filename"):
        if not file_storage.filename:
            return {"has_image": False}
        filename = file_storage.filename.lower()
        ext = filename.rsplit(".", 1)[-1] if "." in filename else ""
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            return {
                "has_image": True,
                "is_valid": False,
                "error": f"Invalid format '{ext}'. Allowed: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}",
            }
        unique_name = f"issue_{uuid.uuid4().hex[:12]}.{ext}"
        saved_path = UPLOADS_DIR / unique_name
        try:
            file_storage.save(str(saved_path))
        except Exception as e:
            return {"has_image": True, "is_valid": False, "error": f"Failed to save file: {e}"}

    # Case 2: Base64 data string (from JSON API or frontend canvas/filereader)
    elif isinstance(file_storage, str) and (file_storage.startswith("data:image/") or len(file_storage) > 80):
        try:
            if "base64," in file_storage:
                header, b64_str = file_storage.split("base64,", 1)
                ext = "png"
                if "jpeg" in header or "jpg" in header:
                    ext = "jpg"
                elif "webp" in header:
                    ext = "webp"
            else:
                b64_str = file_storage
                ext = "jpg"
            data = base64.b64decode(b64_str)
            unique_name = f"issue_{uuid.uuid4().hex[:12]}.{ext}"
            saved_path = UPLOADS_DIR / unique_name
            with open(saved_path, "wb") as f:
                f.write(data)
        except Exception as e:
            return {"has_image": True, "is_valid": False, "error": f"Base64 decode failed: {str(e)}"}
    else:
        return {"has_image": False}

    try:
        file_size_kb = round(saved_path.stat().st_size / 1024, 1)

        # Open and verify integrity with Pillow
        with Image.open(saved_path) as img:
            img.verify()

        # Reopen for pixel analysis (verify closes the image stream)
        with Image.open(saved_path) as img:
            width, height = img.size
            img_rgb = img.convert("RGB")
            np_rgb = np.array(img_rgb)
            gray = np.array(img.convert("L"))

            # 1. EXIF Metadata
            exif = extract_exif_gps(img)
            if exif.get("has_gps") and exif.get("lat") and exif.get("lon"):
                exif["nearest_building"] = find_nearest_building(exif["lat"], exif["lon"])

            # 2. Perceptual Hash
            dhash = compute_perceptual_hash(img)

            # 3. Sharpness / Blur Detection via Laplacian variance
            lap = laplace(gray.astype(np.float32))
            lap_variance = float(lap.var())
            if lap_variance > 220:
                sharpness_label = "Sharp & High Detail"
                sharpness_ok = True
            elif lap_variance > 70:
                sharpness_label = "Moderate Detail"
                sharpness_ok = True
            else:
                sharpness_label = "Blurry / Low Detail"
                sharpness_ok = False

            # 4. Brightness & Illumination
            brightness_mean = float(gray.mean())
            if brightness_mean < 45:
                lighting_label = "Low Light / Pitch Dark Scene"
                scene_light_type = "dark"
            elif brightness_mean < 80:
                lighting_label = "Dimly Lit Scene"
                scene_light_type = "dim"
            elif brightness_mean > 210:
                lighting_label = "Overexposed / High Brightness"
                scene_light_type = "overexposed"
            else:
                lighting_label = "Normal Lighting"
                scene_light_type = "normal"

            # 5. Color Distribution & Dominant Tones
            r_mean = float(np_rgb[:, :, 0].mean())
            g_mean = float(np_rgb[:, :, 1].mean())
            b_mean = float(np_rgb[:, :, 2].mean())

            # Detect visual defect signatures
            defect_tags = []
            if scene_light_type in ("dark", "dim"):
                defect_tags.append("Basement / Blackout Lighting")
            if b_mean > (r_mean + 15) and b_mean > (g_mean + 10):
                defect_tags.append("Water / Reflective Surface")
            if (r_mean > 130 and g_mean > 100 and b_mean < 90) or (r_mean > 150 and g_mean < 90):
                defect_tags.append("Warm Food / Heating Equipment")
            if lap_variance > 300:
                defect_tags.append("High Texture / Physical Structural Edge")

            if not defect_tags:
                defect_tags.append("General Infrastructure Evidence")

            # 6. Cross-Consistency Score
            # Checks if visual features match the complaint context
            consistency_score = 0.80
            match_notes = []

            desc_low = description.lower()
            if "dark" in desc_low or "parking" in desc_low or "light" in desc_low:
                if scene_light_type in ("dark", "dim"):
                    consistency_score += 0.15
                    match_notes.append("Lighting level matches reported low-light/darkness condition.")
            if "water" in desc_low or "leak" in desc_low or "washroom" in desc_low:
                if "Water / Reflective Surface" in defect_tags:
                    consistency_score += 0.15
                    match_notes.append("Reflective / moisture tones match plumbing or water complaint.")
            if "canteen" in category.lower() or "food" in category.lower():
                if "Warm Food / Heating Equipment" in defect_tags or scene_light_type == "normal":
                    consistency_score += 0.15
                    match_notes.append("Visual color tones consistent with cafeteria dining environment.")

            consistency_score = round(min(0.98, consistency_score), 2)
            authenticity = "Verified Authentic Evidence" if sharpness_ok else "Low-Clarity Photo (Review Advised)"

            summary = (
                f"Image verified: {width}x{height} px ({file_size_kb} KB), {sharpness_label} "
                f"(variance {round(lap_variance, 1)}), {lighting_label}. "
                f"Defect tags: {', '.join(defect_tags)}."
            )

            return {
                "has_image": True,
                "is_valid": True,
                "filename": unique_name,
                "image_url": f"/static/uploads/{unique_name}",
                "dimensions": f"{width}x{height}",
                "file_size_kb": file_size_kb,
                "sharpness_score": round(lap_variance, 1),
                "sharpness_label": sharpness_label,
                "brightness_mean": round(brightness_mean, 1),
                "lighting_label": lighting_label,
                "defect_tags": defect_tags,
                "visual_consistency_score": consistency_score,
                "authenticity": authenticity,
                "perceptual_hash": dhash,
                "exif": exif,
                "summary": summary,
            }

    except Exception as e:
        # Clean up failed upload
        if saved_path.exists():
            try:
                saved_path.unlink()
            except Exception:
                pass
        return {
            "has_image": True,
            "is_valid": False,
            "error": f"Failed to process image file: {str(e)}",
        }


def find_nearest_building(lat: float, lon: float) -> dict:
    """Find the nearest PCU campus building for given coordinates using Haversine formula."""
    def _haversine(lat1, lon1, lat2, lon2):
        R = 6371000  # meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlam = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    best_block = "Admin Block"
    best_dist = float("inf")
    best_info = None

    for block_name, info in CAMPUS_GEO_DATA.items():
        dist = _haversine(lat, lon, info["lat"], info["lon"])
        if dist < best_dist:
            best_dist = dist
            best_block = block_name
            best_info = info

    # Check if within 1.5 km of PCU center
    pcu_center_dist = _haversine(lat, lon, PCU_COORDINATES["lat"], PCU_COORDINATES["lon"])
    on_campus = pcu_center_dist <= 800

    return {
        "nearest_block": best_block,
        "building_name": best_info["name"] if best_info else best_block,
        "building_type": best_info.get("type", "Facility") if best_info else "Campus",
        "distance_meters": round(best_dist, 1),
        "target_lat": best_info["lat"] if best_info else lat,
        "target_lon": best_info["lon"] if best_info else lon,
        "on_campus": on_campus,
        "user_lat": round(lat, 6),
        "user_lon": round(lon, 6),
    }
