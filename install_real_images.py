import shutil, json, sqlite3, base64
from pathlib import Path
from civic_sense.image_analyzer import analyze_image
from civic_sense.classifier import load_classifier
from civic_sense.prioritizer import assign_priority

brain = Path('C:/Users/ashra/.gemini/antigravity-ide/brain/3534f954-3e9a-4907-90be-e25f7bdafe5c')
uploads = Path('static/uploads')
uploads.mkdir(parents=True, exist_ok=True)

images_to_install = {
    'pcu_elevator_sparking.jpg': 'elevator_sparking_switchboard_1791855599441.jpg',
    'pcu_projector_broken.jpg': 'broken_classroom_projector_1791855668013.jpg',
    'pcu_washroom_leak.jpg': 'washroom_water_leakage_1791855699105.jpg',
    'pcu_canteen_hygiene.jpg': 'canteen_food_quality_1791855727437.jpg',
    'pcu_hostel_geyser.jpg': 'hostel_geyser_leak_1791855756738.jpg',
}

analyses = {}
for target_name, src_name in images_to_install.items():
    src_file = brain / src_name
    dest_file = uploads / target_name
    if src_file.exists():
        shutil.copy2(src_file, dest_file)
        with open(dest_file, "rb") as f:
            b64 = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()
        res = analyze_image(b64)
        res["image_url"] = f"/static/uploads/{target_name}"
        res["filename"] = target_name
        analyses[target_name] = res
        print(f"Installed {target_name}: {res.get('dimensions')}, sharp={res.get('sharpness_score')}, tags={res.get('defect_tags')}")

conn = sqlite3.connect('data/civicsense.db')
c = conn.cursor()

# 1. Update Elevator complaint
c.execute("""
    UPDATE complaints 
    SET priority = 'High',
        confidence = 0.801,
        image_url = '/static/uploads/pcu_elevator_sparking.jpg',
        image_analysis = ?
    WHERE description LIKE '%Elevator is making loud grinding noises%'
""", (json.dumps(analyses.get('pcu_elevator_sparking.jpg', {})),))

# 2. Update Projector complaints
c.execute("""
    UPDATE complaints
    SET image_url = '/static/uploads/pcu_projector_broken.jpg',
        image_analysis = ?
    WHERE (description LIKE '%projector%' OR title LIKE '%projector%')
""", (json.dumps(analyses.get('pcu_projector_broken.jpg', {})),))

# 3. Update Washroom leakage complaints
c.execute("""
    UPDATE complaints
    SET image_url = '/static/uploads/pcu_washroom_leak.jpg',
        image_analysis = ?
    WHERE (description LIKE '%washroom%' OR description LIKE '%water tap%' OR description LIKE '%seepage%')
""", (json.dumps(analyses.get('pcu_washroom_leak.jpg', {})),))

# 4. Update Canteen food quality complaints
c.execute("""
    UPDATE complaints
    SET image_url = '/static/uploads/pcu_canteen_hygiene.jpg',
        image_analysis = ?
    WHERE (description LIKE '%canteen%' OR description LIKE '%food%' OR description LIKE '%rice%')
""", (json.dumps(analyses.get('pcu_canteen_hygiene.jpg', {})),))

# 5. Update Hostel geyser complaints
c.execute("""
    UPDATE complaints
    SET image_url = '/static/uploads/pcu_hostel_geyser.jpg',
        image_analysis = ?
    WHERE (description LIKE '%geyser%' OR description LIKE '%hot water%')
""", (json.dumps(analyses.get('pcu_hostel_geyser.jpg', {})),))

conn.commit()

# Re-score all complaints with calibrated classifier & prioritizer
classifier, _ = load_classifier()
rows = c.execute("SELECT id, description, category, ward, created_at FROM complaints").fetchall()
updated_count = 0
for cid, desc, cat, ward, created in rows:
    new_cat, new_conf = classifier(desc or '')
    new_p, _, _ = assign_priority(desc or '', new_cat, ward, created)
    c.execute("UPDATE complaints SET confidence = ?, priority = ? WHERE id = ?", (new_conf, new_p, cid))
    updated_count += 1
conn.commit()
print(f"Re-scored {updated_count} complaints with calibrated confidence and priority.")

elev = c.execute("SELECT id, title, priority, confidence, image_url FROM complaints WHERE description LIKE '%Elevator is making loud grinding noises%' LIMIT 1").fetchone()
print("Elevator complaint in DB:", elev)
conn.close()
