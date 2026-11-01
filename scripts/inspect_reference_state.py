"""Read the catalog inbox and detect edited copies before slide authoring."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import posixpath
import sys
import xml.etree.ElementTree as E
from zipfile import BadZipFile, ZipFile

P = "http://schemas.openxmlformats.org/presentationml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
N = {"p": P, "a": A, "r": R}
INBOX_NOTES = "补充入口：将新的元素或排版放在本页空白处，或添加在本页之后。每次使用Skill时先检查此处，有内容则先脱敏、归类和更新索引，再制作PPT。此页本身不计入模板数量。"

def sha256(path: Path) -> str:
    """Return a content digest without changing the source."""
    return hashlib.sha256(path.read_bytes()).hexdigest()

def relationship_map(archive: ZipFile, owner: str) -> dict[str, tuple[str, str]]:
    """Resolve internal part relationships, ignoring external links."""
    owner_path = PurePosixPath(owner)
    part = str(owner_path.parent / "_rels" / (owner_path.name + ".rels"))
    if part not in archive.namelist():
        return {}
    rels = E.fromstring(archive.read(part))
    return {rel.get("Id", ""): (posixpath.normpath(posixpath.join(str(owner_path.parent), rel.get("Target", ""))), rel.get("Type", "")) for rel in rels if rel.get("TargetMode") != "External"}

def inspect_catalog(path: Path) -> dict:
    """Find pasted objects and appended slides at the maintained supplement marker."""
    with ZipFile(path) as archive:
        presentation = E.fromstring(archive.read("ppt/presentation.xml"))
        relationships = relationship_map(archive, "ppt/presentation.xml")
        slides = []
        for item in presentation.findall("p:sldIdLst/p:sldId", N):
            part = relationships[item.get(f"{{{R}}}id")][0]
            slides.append((part, E.fromstring(archive.read(part))))
        markers = []
        for index, (_, slide) in enumerate(slides, 1):
            names = [node.get("name", "") for node in slide.findall(".//p:cNvPr", N)]
            if "supplement-inbox-start" in names or slide.find("p:cSld", N).get("name") == "补充模板放置区":
                markers.append(index)
        if len(markers) != 1:
            return {"slide_count": len(slides), "inbox_marker_count": len(markers), "pending_pages": [], "needs_reconciliation": True}
        start = markers[0]
        pending = []
        for number, (part, slide) in enumerate(slides[start - 1:], start):
            nodes = []
            tree = slide.find("p:cSld/p:spTree", N)
            for node in list(tree)[2:]:
                prop = node.find(".//p:cNvPr", N)
                if prop is not None and prop.get("name") == "supplement-inbox-start":
                    # A renamed or edited marker can contain a user-supplied addition.
                    texts = "".join(t.text or "" for t in node.findall(".//a:t", N))
                    if texts != "补充模板":
                        nodes.append(node)
                    continue
                if node.find(".//p:ph", N) is not None and not any((t.text or "").strip() for t in node.findall(".//a:t", N)):
                    continue
                nodes.append(node)
            notes_text = ""
            for target, kind in relationship_map(archive, part).values():
                if kind.endswith("/notesSlide"):
                    notes = E.fromstring(archive.read(target))
                    for shape in notes.findall(".//p:sp", N):
                        ph = shape.find(".//p:ph", N)
                        if ph is not None and ph.get("type") == "body":
                            notes_text = "".join(t.text or "" for t in shape.findall(".//a:t", N))
            notes_changed = bool(notes_text.strip()) and (number != start or notes_text.strip() != INBOX_NOTES)
            if nodes or notes_changed:
                pending.append({"page": number, "objects": len(nodes), "notes_added": notes_changed, "hidden": slide.get("show") == "0"})
        return {"slide_count": len(slides), "inbox_marker_count": 1, "inbox_start_page": start, "pending_pages": pending, "needs_reconciliation": False}

def inspect_state(skill_root: Path, working_copy: Path | None = None) -> dict:
    """Choose the edited catalog while protecting independently changed copies."""
    config_path = skill_root / ".local/resource-paths.json"
    config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    installed = skill_root / "assets/element-reference.pptx"
    working = working_copy or (Path(config["catalog_working_copy"]) if config.get("catalog_working_copy") else None)
    installed_digest = sha256(installed)
    working_digest = sha256(working) if working and working.exists() else None
    baseline = config.get("last_synced_catalog_sha256", installed_digest)
    installed_changed, working_changed = installed_digest != baseline, working_digest is not None and working_digest != baseline
    conflict = bool(installed_changed and working_changed and installed_digest != working_digest)
    selected = working if working_changed and not conflict else installed
    result = {"catalog_path": str(selected), "catalog_sha256": sha256(selected), "copy_conflict": conflict,
              "needs_sync": sha256(selected) != baseline,
              "working_copy_missing": bool(working and not working.exists()),
              "memory_path": str(skill_root / ".local/Memory.pptx")}
    result.update(inspect_catalog(selected))
    result["ready_for_use"] = not (conflict or result["needs_sync"] or result["needs_reconciliation"] or result["pending_pages"])
    return result

def main() -> None:
    """Print a read-only inventory; status 2 means classification or reconciliation is needed."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--working-copy", type=Path)
    args = parser.parse_args()
    try:
        result = inspect_state(args.skill_root, args.working_copy)
    except (OSError, BadZipFile, E.ParseError, KeyError, ValueError) as error:
        print(json.dumps({"ready_for_use": False, "error": str(error)}, ensure_ascii=False))
        sys.exit(1)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["ready_for_use"] else 2)

if __name__ == "__main__":
    main()
