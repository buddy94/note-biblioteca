#!/usr/bin/env python3
"""
Manifest Generator for GitHub Pages Note Library
=================================================
Scans gh-pages/notes/ for .txt files and regenerates manifest.json.
Run this after adding/removing notes.

Usage:
  python3 gen_manifest.py              # Regenerate manifest
  python3 gen_manifest.py --dry-run    # Show what would change
  python3 gen_manifest.py --add <file> # Add single note interactively
"""

import os, json, re, sys, hashlib
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
NOTES_DIR = BASE_DIR / "notes"
MANIFEST_FILE = BASE_DIR / "manifest.json"

# Category definitions (edit this to add/remove categories)
CATEGORIES = {
    "ai-etica": {
        "name": "AI & Etica",
        "icon": "🤖",
        "parent": "AI & Società",
        "color": "#6366f1",
        "keywords": ["ai", "ia", "intelligenza artificiale", "etica", "algoretica", "robot",
                     "autonoma", "guerra", "transumanesimo", "postumano", "democrazia",
                     "enciclica", "papa", "machine learning", "algoritmo"]
    },
    "idee-riflessioni": {
        "name": "Idee & Riflessioni",
        "icon": "💡",
        "parent": "Fede & Cultura",
        "color": "#f59e0b",
        "keywords": ["filosofia", "paradosso", "identità", "riflessione", "pensiero",
                     "scuola", "comunità", "dunning", "kruger", "mappe", "cuore",
                     "nave", "teseo"]
    },
    "spiritualita-tradizione": {
        "name": "Spiritualità & Tradizione",
        "icon": "🕊️",
        "parent": "Fede & Cultura",
        "color": "#10b981",
        "keywords": ["fede", "tradizione", "spiritualità", "genz", "architettura",
                     "incontro", "preghiera", "chiesa", "dio", "cristiano"]
    },
    "tolkien": {
        "name": "Tolkien",
        "icon": "🧙‍♂️",
        "parent": "Fede & Cultura",
        "color": "#8b5cf6",
        "keywords": ["tolkien", "signore degli anelli", "aragorn", "galadriel",
                     "samwise", "gamgee", "théoden", "inkl", "chesterton",
                     "middle earth", "hobbit", "silmarillion"]
    },
    "genitorialita": {
        "name": "Genitorialità",
        "icon": "👨‍👧‍👦",
        "parent": "Famiglia & Figli",
        "color": "#ef4444",
        "keywords": ["genitorialità", "padre", "figli", "fratelli", "competizione",
                     "autorevolezza", "emotivo", "minacce", "condizionali", "coerenza",
                     "educazione", "bambini", "genitori"]
    },
}

def extract_title(md_path):
    """Extract title from markdown file: first # heading or filename"""
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('# ') and not line.startswith('## '):
                    return line[2:].strip()
    except:
        pass
    # Fallback: use filename
    name = md_path.stem.replace('-', ' ').replace('_', ' ')
    return name.title()

def auto_categorize(note_path, title, content_preview=None):
    """Auto-assign category based on keyword matching"""
    text = title.lower()
    if content_preview:
        text += ' ' + content_preview.lower()
    
    scores = {}
    for cat_key, cat_def in CATEGORIES.items():
        score = 0
        for kw in cat_def.get("keywords", []):
            if kw.lower() in text:
                score += 1
        if score > 0:
            scores[cat_key] = score
    
    if not scores:
        return None, 0
    
    # Return category with highest score
    best = max(scores, key=scores.get)
    return best, scores[best]

def scan_notes():
    """Scan notes directory and return note definitions"""
    notes = []
    for md_file in sorted(NOTES_DIR.glob("*.txt")):
        title = extract_title(md_file)
        
        # Read first 500 chars for auto-categorization
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read(500)
        except:
            content = ""
        
        notes.append({
            "filename": md_file.name,
            "title": title,
            "path": str(md_file)
        })
    
    return notes

def load_manifest():
    """Load existing manifest or create empty one"""
    if MANIFEST_FILE.exists():
        with open(MANIFEST_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"categories": {}, "notes": []}

def save_manifest(manifest):
    """Save manifest to file"""
    with open(MANIFEST_FILE, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

def interactive_add(note_file):
    """Interactive mode: prompt for category assignment"""
    note_path = Path(note_file)
    if not note_path.exists():
        print(f"❌ File not found: {note_file}")
        return
    
    # Copy to notes dir
    import shutil
    safe_name = re.sub(r'[^a-zA-Z0-9\-]', '-', note_path.stem.lower())
    safe_name = re.sub(r'-+', '-', safe_name).strip('-') + '.txt'
    dst = NOTES_DIR / safe_name
    shutil.copy2(note_path, dst)
    print(f"📄 Copied: {note_path.name} → {safe_name}")
    
    title = extract_title(dst)
    cat_key, score = auto_categorize(dst, title)
    
    print(f"\n📝 Title: {title}")
    print(f"🤖 Auto-detected category: {CATEGORIES.get(cat_key, {}).get('name', 'None')} (score: {score})")
    print(f"\nAvailable categories:")
    for i, (k, v) in enumerate(CATEGORIES.items(), 1):
        print(f"  {i}. {v['icon']} {v['name']} ({v['parent']})")
    print(f"  0. Create NEW category")
    
    choice = input(f"\nChoose category [1-{len(CATEGORIES)}, 0=new, Enter=auto]: ").strip()
    
    if choice == '0':
        # Create new category
        new_name = input("Category name: ")
        new_icon = input("Icon (emoji): ")
        new_parent = input("Parent category: ")
        new_color = input("Color (#hex): ")
        new_keywords = input("Keywords (comma-separated): ").split(',')
        
        cat_key = re.sub(r'[^a-z0-9\-]', '-', new_name.lower().strip())
        cat_key = re.sub(r'-+', '-', cat_key).strip('-')
        
        CATEGORIES[cat_key] = {
            "name": new_name,
            "icon": new_icon or "📄",
            "parent": new_parent or "Altro",
            "color": new_color or "#6366f1",
            "keywords": [kw.strip() for kw in new_keywords if kw.strip()]
        }
        print(f"✅ New category created: {cat_key}")
    elif choice and choice.isdigit():
        idx = int(choice) - 1
        cat_key = list(CATEGORIES.keys())[idx]
    
    if not cat_key:
        print("❌ No category assigned. Using 'idee-riflessioni' as default.")
        cat_key = "idee-riflessioni"
    
    # Update manifest
    manifest = load_manifest()
    manifest["categories"] = CATEGORIES
    
    # Remove existing entry for this file
    manifest["notes"] = [n for n in manifest["notes"] if n["filename"] != safe_name]
    
    manifest["notes"].append({
        "filename": safe_name,
        "title": title,
        "category": cat_key,
        "category_name": CATEGORIES[cat_key]["name"],
        "parent_category": CATEGORIES[cat_key]["parent"],
    })
    
    # Sort notes by title
    manifest["notes"].sort(key=lambda n: n["title"].lower())
    
    save_manifest(manifest)
    print(f"✅ Manifest updated! Note added to: {CATEGORIES[cat_key]['name']}")
    print(f"📋 Total notes: {len(manifest['notes'])}")

def regenerate(dry_run=False):
    """Full regeneration of manifest"""
    notes = scan_notes()
    manifest = load_manifest()
    
    # Preserve existing category assignments for known files
    existing_map = {n["filename"]: n for n in manifest.get("notes", [])}
    
    new_notes = []
    new_categories_needed = []
    
    for note in notes:
        if note["filename"] in existing_map:
            # Preserve existing assignment
            entry = existing_map[note["filename"]].copy()
            entry["title"] = note["title"]  # Update title in case file changed
            new_notes.append(entry)
        else:
            # New note - auto-categorize
            cat_key, score = auto_categorize(note["path"], note["title"])
            if cat_key and cat_key in CATEGORIES:
                cat = CATEGORIES[cat_key]
                new_notes.append({
                    "filename": note["filename"],
                    "title": note["title"],
                    "category": cat_key,
                    "category_name": cat["name"],
                    "parent_category": cat["parent"],
                })
                print(f"🆕 {note['filename']} → {cat['name']} (score: {score})")
            else:
                print(f"⚠️  {note['filename']} → No category match! Needs manual assignment.")
                new_notes.append({
                    "filename": note["filename"],
                    "title": note["title"],
                    "category": "idee-riflessioni",
                    "category_name": "Idee & Riflessioni",
                    "parent_category": "Fede & Cultura",
                })
    
    manifest["categories"] = CATEGORIES
    manifest["notes"] = sorted(new_notes, key=lambda n: n["title"].lower())
    
    if dry_run:
        print(f"\n📊 DRY RUN — Would update manifest:")
        print(f"   Categories: {len(CATEGORIES)}")
        print(f"   Notes: {len(new_notes)}")
        print(f"   New: {len([n for n in notes if n['filename'] not in existing_map])}")
        print(f"   Orphaned: {len([f for f in existing_map if f not in [n['filename'] for n in notes]])}")
    else:
        save_manifest(manifest)
        print(f"\n✅ Manifest regenerated: {len(CATEGORIES)} categories, {len(new_notes)} notes")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--add":
        if len(sys.argv) < 3:
            print("Usage: python3 gen_manifest.py --add <file.txt>")
            sys.exit(1)
        interactive_add(sys.argv[2])
    elif len(sys.argv) > 1 and sys.argv[1] == "--dry-run":
        regenerate(dry_run=True)
    else:
        regenerate()
