#!/usr/bin/env python3
"""
ClickHouse client upgrade checker.
Fetches Maven versions, selects latest within major, parses changelog, categorizes by risk/area.
"""

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.request import urlopen, Request

# maven-metadata.xml lists ALL versions; Maven Search API returns limited/aggregated results
MAVEN_METADATA_URL = "https://repo1.maven.org/maven2/com/clickhouse/client-v2/maven-metadata.xml"
CHANGELOG_URL = "https://raw.githubusercontent.com/ClickHouse/clickhouse-java/main/CHANGELOG.md"

# Risk mapping: changelog section -> risk level
SECTION_RISK = {
    "Dependencies": "High",
    "Important Changes": "High",
    "Bug Fixes": "Medium",
    "New Features": "Low",
    "Improvements": "Low",
    "Misc": "Low",
    "Docs": "Low",
}

# Area tag -> display name (supports multiple tags like "client-v2, jdbc-v2")
AREA_NAMES = {
    "client-v2": "Client API",
    "jdbc-v2": "JDBC Driver",
    "repo": "Dependencies",
    "client-v1": "Legacy Client",
    "jdbc": "JDBC Driver",
    "jbdc-v2": "JDBC Driver",  # typo in changelog
    "client-v2, jdbc-v2": "Client API / JDBC Driver",
}


def fetch_text(url: str) -> str:
    req = Request(url, headers={"User-Agent": "ClickHouse-Upgrade-Check/1.0"})
    with urlopen(req, timeout=15) as r:
        return r.read().decode()


def parse_version(v: str) -> tuple:
    """Parse version to (major, minor, patch) for comparison. Excludes -patchN, -SNAPSHOT."""
    base = re.split(r"[-+]", v)[0]
    parts = base.split(".")
    major = int(parts[0]) if len(parts) > 0 else 0
    minor = int(parts[1]) if len(parts) > 1 else 0
    patch = int(parts[2]) if len(parts) > 2 else 0
    return (major, minor, patch)


def is_release_version(v: str) -> bool:
    """Exclude patch, snapshot, rc versions from upgrade selection."""
    return not any(
        x in v.lower()
        for x in ["-patch", "-snapshot", "-rc", "-alpha", "-beta", "-m"]
    )


def get_maven_versions() -> list[str]:
    """Fetch all versions from maven-metadata.xml (complete list; Search API omits patch versions)."""
    xml_text = fetch_text(MAVEN_METADATA_URL)
    root = ET.fromstring(xml_text)
    # maven-metadata.xml: metadata/versioning/versions/version
    versions_el = root.find("versioning/versions")
    if versions_el is None:
        versions_el = root.find(".//versions")
    parent = versions_el if versions_el is not None else root
    versions = [v.text for v in parent.findall("version") if v.text]
    return [v for v in versions if is_release_version(v)]


def get_target_version(current: str, available: list[str]) -> str | None:
    """Latest version with same major as current."""
    curr_parts = parse_version(current)
    major = curr_parts[0], curr_parts[1]  # 0.x -> (0, x)

    candidates = []
    for v in available:
        p = parse_version(v)
        if (p[0], p[1]) == major and parse_version(v) >= curr_parts:
            candidates.append(v)

    if not candidates:
        return None
    candidates.sort(key=parse_version, reverse=True)
    return candidates[0]


def get_current_version(toml_path: Path | None) -> str | None:
    """Read current version from libs.versions.toml."""
    if not toml_path or not toml_path.exists():
        return None
    text = toml_path.read_text()
    m = re.search(r'clickhouse-java\s*=\s*["\']([^"\']+)["\']', text)
    return m.group(1) if m else None


def parse_changelog(changelog: str, from_ver: str, to_ver: str) -> list[dict]:
    """
    Extract changes between from_ver (exclusive) and to_ver (inclusive).
    Returns list of {version, section, risk, area, text, link}.
    """
    from_parts = parse_version(from_ver)
    to_parts = parse_version(to_ver)
    entries = []

    current_version = None
    current_section = None
    version_pattern = re.compile(r"^##\s+(\d+\.\d+\.\d+)", re.M)
    section_pattern = re.compile(r"^###\s+(.+)", re.M)
    entry_pattern = re.compile(r"^-\s+\[([^\]]*)\]\s*(.+?)(?:\s*\((\S+)\))?\s*$", re.M)
    link_pattern = re.compile(r"\((https://[^)]+)\)")

    lines = changelog.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        vm = version_pattern.match(line.strip())
        if vm:
            v = vm.group(1)
            vp = parse_version(v)
            if from_parts < vp <= to_parts:
                current_version = v
                current_section = None
            else:
                current_version = None
            i += 1
            continue

        sm = section_pattern.match(line.strip())
        if sm and current_version:
            current_section = sm.group(1).strip()
            i += 1
            continue

        em = entry_pattern.match(line.strip())
        if em and current_version and current_section:
            area = em.group(1).strip() or "repo"
            text = em.group(2).strip()
            link = em.group(3) or ""
            if not link:
                lm = link_pattern.search(line)
                link = lm.group(1) if lm else ""
            risk = SECTION_RISK.get(current_section, "Low")
            entries.append(
                {
                    "version": current_version,
                    "section": current_section,
                    "risk": risk,
                    "area": area,
                    "text": text,
                    "link": link,
                }
            )
        elif line.strip().startswith("- ") and current_version and current_section:
            # Multi-line or alternate format
            raw = line.strip()[2:]
            area_m = re.search(r"\[([^\]]*)\]", raw)
            area = area_m.group(1) if area_m else "repo"
            text = re.sub(r"\[[^\]]*\]\s*", "", raw, count=1)
            link_m = link_pattern.search(raw)
            link = link_m.group(1) if link_m else ""
            risk = SECTION_RISK.get(current_section, "Low")
            entries.append(
                {
                    "version": current_version,
                    "section": current_section,
                    "risk": risk,
                    "area": area,
                    "text": text,
                    "link": link,
                }
            )
        i += 1

    return entries


def format_summary(current: str, target: str, entries: list[dict]) -> str:
    major = f"{parse_version(current)[0]}.{parse_version(current)[1]}"

    by_risk = {"High": [], "Medium": [], "Low": []}
    by_area = {}
    for e in entries:
        by_risk[e["risk"]].append(e)
        area_name = AREA_NAMES.get(e["area"], e["area"])
        if area_name not in by_area:
            by_area[area_name] = []
        by_area[area_name].append(e)

    lines = [
        f"# ClickHouse Client Upgrade: {current} → {target}",
        "",
        "## Summary",
        f"- **Current**: {current}",
        f"- **Target**: {target} (latest within major {major})",
        "",
        "## Changes by Risk",
        "",
    ]

    for risk in ["High", "Medium", "Low"]:
        items = by_risk[risk]
        if items:
            lines.append(f"### {risk}")
            for e in items:
                area = AREA_NAMES.get(e["area"], e["area"])
                link = f" ({e['link']})" if e["link"] else ""
                lines.append(f"- [{area}] {e['text']}{link}")
            lines.append("")

    lines.append("## Changes by Area")
    lines.append("")
    for area_name in sorted(by_area.keys()):
        items = by_area[area_name]
        lines.append(f"### {area_name}")
        for e in items:
            link = f" ({e['link']})" if e["link"] else ""
            lines.append(f"- [{e['risk']}] {e['text']}{link}")
        lines.append("")

    return "\n".join(lines)


def apply_upgrade(toml_path: Path, new_version: str) -> None:
    text = toml_path.read_text()
    text = re.sub(
        r'(clickhouse-java\s*=\s*)["\'][^"\']+["\']',
        f'\\1"{new_version}"',
        text,
    )
    toml_path.write_text(text)


def main() -> int:
    parser = argparse.ArgumentParser(description="ClickHouse client upgrade checker")
    parser.add_argument(
        "--toml",
        type=Path,
        default=Path("gradle/libs.versions.toml"),
        help="Path to libs.versions.toml",
    )
    parser.add_argument(
        "--current",
        type=str,
        help="Override current version (skip reading from toml)",
    )
    parser.add_argument(
        "--versions-only",
        action="store_true",
        help="Only list available Maven versions",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply upgrade to libs.versions.toml",
    )
    args = parser.parse_args()

    if args.versions_only:
        versions = get_maven_versions()
        for v in sorted(versions, key=parse_version, reverse=True):
            print(v)
        return 0

    current = args.current or get_current_version(args.toml)
    if not current:
        print("Could not determine current version. Use --current X.Y.Z or ensure --toml path is correct.", file=sys.stderr)
        return 1

    versions = get_maven_versions()
    target = get_target_version(current, versions)

    if not target:
        print(f"No newer version within same major as {current}. Available: {versions[:5]}...")
        return 0

    if target == current:
        print(f"Already at latest within major version: {current}")
        return 0

    changelog = fetch_text(CHANGELOG_URL)
    entries = parse_changelog(changelog, current, target)

    summary = format_summary(current, target, entries)
    print(summary)

    if args.apply and args.toml.exists():
        apply_upgrade(args.toml, target)
        print(f"\nUpdated {args.toml} to {target}")
    elif args.apply:
        print("\n--apply specified but toml file not found.", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
