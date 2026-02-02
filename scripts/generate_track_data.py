#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "requests",
#     "jinja2",
# ]
# ///
"""
Generate TrackData.lua from wago.tools DB2 data.

Fetches bonus ID to upgrade track mappings from:
- ItemBonusSeasonBonusListGroup (contains track number per group)
- ItemBonusListGroupEntry (maps group ID to bonus IDs)

Maps track numbers to names:
1=Explorer, 2=Adventurer, 3=Veteran, 4=Champion, 5=Hero, 6=Myth

Usage: uv run scripts/generate_track_data.py
       uv run scripts/generate_track_data.py --force  # Skip version check
"""

import argparse
import re
import requests
import sys
from pathlib import Path
from jinja2 import Template

# wago.tools DB2 API endpoints
WAGO_BASE = "https://wago.tools/db2"

# Track number to name mapping
TRACK_NAMES = {
    1: "explorer",
    2: "adventurer",
    3: "veteran",
    4: "champion",
    5: "hero",
    6: "myth",
}


def fetch_current_build() -> str | None:
    """Fetch the current WoW retail build version from wago.tools."""
    # Fetch from wago.tools builds API
    # Response format: {"wow": [{version: "...", ...}, ...], "wow_beta": [...], ...}
    try:
        response = requests.get("https://wago.tools/api/builds", timeout=10)
        response.raise_for_status()
        builds = response.json()
        # Get retail builds (key "wow"), first entry is latest
        wow_builds = builds.get("wow", [])
        if wow_builds and len(wow_builds) > 0:
            return wow_builds[0].get("version", "")
    except (requests.RequestException, ValueError, KeyError, AttributeError):
        pass

    return None


def get_existing_build(output_path: Path) -> str | None:
    """Extract build version from existing TrackData.lua file."""
    if not output_path.exists():
        return None

    try:
        content = output_path.read_text()
        # Look for: -- Build: X.X.X.XXXXX
        match = re.search(r"^-- Build: (.+)$", content, re.MULTILINE)
        if match:
            return match.group(1).strip()
    except (OSError, IOError):
        pass

    return None


def should_regenerate(output_path: Path, force: bool = False) -> tuple[bool, str]:
    """
    Check if TrackData.lua needs regeneration.

    Returns (should_regenerate, reason).
    """
    if force:
        return True, "forced regeneration"

    if not output_path.exists():
        return True, "TrackData.lua does not exist"

    existing_build = get_existing_build(output_path)
    if not existing_build:
        return True, "could not determine existing build version"

    current_build = fetch_current_build()
    if not current_build:
        print("Warning: Could not fetch current build version, skipping regeneration")
        return False, "could not fetch current build"

    if existing_build != current_build:
        return True, f"build changed: {existing_build} -> {current_build}"

    return False, f"already up to date (build {existing_build})"


def fetch_db2_table(table_name: str) -> list:
    """Fetch a DB2 table from wago.tools API."""
    url = f"{WAGO_BASE}/{table_name}/csv"
    print(f"Fetching {table_name}...")

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching {table_name}: {e}")
        return []

    lines = response.text.strip().split("\n")
    if len(lines) < 2:
        return []

    headers = lines[0].split(",")
    rows = []

    for line in lines[1:]:
        if not line.strip():
            continue
        values = line.split(",")
        row = {}
        for i, header in enumerate(headers):
            if i < len(values):
                row[header.strip()] = values[i].strip()
        rows.append(row)

    return rows


def build_track_mapping() -> dict:
    """
    Build bonus ID to track name mapping.

    Chain: ItemBonusSeasonBonusListGroup (track + group) -> ItemBonusListGroupEntry (group -> bonus IDs)
    """

    # Fetch required tables
    bonus_list_groups = fetch_db2_table("ItemBonusSeasonBonusListGroup")
    group_entries = fetch_db2_table("ItemBonusListGroupEntry")

    if not bonus_list_groups or not group_entries:
        print("Warning: Failed to fetch required tables")
        return {}

    # Build group ID -> track number mapping
    # Field_10_1_0_48898_002 contains the track number
    group_to_track = {}
    for row in bonus_list_groups:
        group_id = row.get("ItemBonusListGroupID", "")
        # Track number is in Field_10_1_0_48898_002
        track_num = row.get("Field_10_1_0_48898_002", "")
        if group_id and track_num:
            try:
                gid = int(group_id)
                tnum = int(track_num)
                if tnum in TRACK_NAMES:
                    group_to_track[gid] = tnum
            except ValueError:
                continue

    print(f"Found {len(group_to_track)} groups with valid track numbers")

    # Build group ID -> [bonus IDs] mapping
    group_to_bonuses = {}
    for row in group_entries:
        group_id = row.get("ItemBonusListGroupID", "")
        bonus_id = row.get("ItemBonusListID", "")
        if group_id and bonus_id:
            try:
                gid = int(group_id)
                bid = int(bonus_id)
                if gid not in group_to_bonuses:
                    group_to_bonuses[gid] = []
                group_to_bonuses[gid].append(bid)
            except ValueError:
                continue

    print(f"Found {len(group_to_bonuses)} groups with bonus entries")

    # Build final bonus_id -> track_name mapping
    bonus_to_track = {}
    for group_id, track_num in group_to_track.items():
        track_name = TRACK_NAMES.get(track_num)
        if not track_name:
            continue

        bonus_ids = group_to_bonuses.get(group_id, [])
        for bonus_id in bonus_ids:
            bonus_to_track[bonus_id] = track_name

    print(f"Mapped {len(bonus_to_track)} bonus IDs to tracks")

    return bonus_to_track


def generate_lua(bonus_to_track: dict, output_path: Path, build_version: str):
    """Generate TrackData.lua from the mapping."""

    template_path = Path(__file__).parent / "TrackData.template"

    if not template_path.exists():
        print(f"Error: Template not found at {template_path}")
        sys.exit(1)

    with open(template_path, "r") as f:
        template = Template(f.read())

    # Sort by bonus ID for consistent output
    sorted_mapping = dict(sorted(bonus_to_track.items()))

    lua_content = template.render(track_ids=sorted_mapping, build_version=build_version)

    with open(output_path, "w") as f:
        f.write(lua_content)

    print(f"Generated {output_path} (build {build_version})")


def main():
    parser = argparse.ArgumentParser(description="Generate TrackData.lua from wago.tools")
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force regeneration even if build version hasn't changed"
    )
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    addon_dir = script_dir.parent
    output_path = addon_dir / "TrackData.lua"

    # Check if regeneration is needed
    should_regen, reason = should_regenerate(output_path, force=args.force)

    if not should_regen:
        print(f"Skipping generation: {reason}")
        return

    print(f"Generating track data from wago.tools ({reason})...")

    # Fetch current build version for embedding
    build_version = fetch_current_build() or "unknown"

    bonus_to_track = build_track_mapping()

    if not bonus_to_track:
        print("Warning: No bonus ID mappings found, generating empty file")

    generate_lua(bonus_to_track, output_path, build_version)

    print("Done!")


if __name__ == "__main__":
    main()
