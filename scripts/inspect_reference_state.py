"""Read the catalog inbox and detect edited copies before slide authoring."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import sys
import tempfile
import unicodedata
import xml.etree.ElementTree as E
from zipfile import BadZipFile, ZipFile

P = "http://schemas.openxmlformats.org/presentationml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
N = {"p": P, "a": A, "r": R}
INBOX_NOTES = "补充入口：将新的元素或排版放在本页空白处，或添加在本页之后。每次使用Skill时先检查此处，有内容则先脱敏、归类和更新索引，再制作PPT。此页本身不计入模板数量。"
SUGGESTION_PREFIX = re.compile(r"^\s*(?:【(?:制作)?建议】|\[(?:制作)?建议\]|(?:制作)?建议\s*[:：])\s*")
RESOLVED_STATUSES = {"applied", "already_covered", "not_applicable"}


def text_content(node: E.Element) -> str:
    """Read paragraphs and soft breaks without executing document content."""
    paragraphs = []
    for paragraph in node.findall(".//a:p", N):
        pieces = []
        for child in paragraph.iter():
            if child.tag == f"{{{A}}}t":
                pieces.append(child.text or "")
            elif child.tag == f"{{{A}}}br":
                pieces.append("\n")
        paragraphs.append("".join(pieces))
    return "\n".join(paragraphs).strip()


def is_page_number(shape: E.Element) -> bool:
    """Recognize native current/total chrome without hiding added advice."""
    ph = shape.find('p:nvSpPr/p:nvPr/p:ph', N)
    field = shape.find('.//a:fld', N)
    return bool(ph is not None and ph.get('type') == 'sldNum'
                and field is not None and field.get('type') == 'slidenum'
                and re.fullmatch(r'\d+/\d+', text_content(shape)))


def feedback_item(text: str, page: int, part: str, source: str,
                  shape: E.Element | None = None) -> dict:
    """Identify stable text items; a marker is a review hint, not permission to act."""
    normalized = unicodedata.normalize("NFKC", text)
    marked = bool(SUGGESTION_PREFIX.match(normalized))
    normalized = SUGGESTION_PREFIX.sub("", normalized, count=1)
    normalized = " ".join(normalized.split())
    content_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    prop = shape.find(".//p:cNvPr", N) if shape is not None else None
    return {"suggestion_id": "S-" + content_hash[:20], "content_hash": content_hash,
            "text": text, "normalized_text": normalized, "marked_suggestion": marked,
            "page": page, "slide_part": part, "source": source,
            "shape_id": prop.get("id") if prop is not None else None,
            "shape_name": prop.get("name") if prop is not None else None}


def history_path(skill_root: Path) -> Path:
    """Keep raw feedback and its processing receipts inside the local-only folder."""
    path = skill_root / ".local/suggestion-history.json"
    if not path.resolve().is_relative_to(skill_root.resolve()):
        raise ValueError("建议记录必须位于本技能的.local目录")
    return path


def read_history(skill_root: Path) -> dict:
    """Read existing receipts without creating an empty record file."""
    path = history_path(skill_root)
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"version": 1, "records": {}}
    if (not isinstance(data, dict) or data.get("version") != 1
            or not isinstance(data.get("records"), dict)
            or any(not isinstance(record, dict) for record in data["records"].values())):
        raise ValueError("建议记录格式无效，请检查本机记录后再处理")
    return data

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

def inspect_catalog(path: Path, records: dict | None = None) -> dict:
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
        text_items = []
        for number, (part, slide) in enumerate(slides[start - 1:], start):
            nodes = []
            tree = slide.find("p:cSld/p:spTree", N)
            for node in list(tree)[2:]:
                if is_page_number(node):
                    continue
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
            for node in nodes:
                shapes = [node] if node.tag == f"{{{P}}}sp" else node.findall(".//p:sp", N)
                for shape in shapes:
                    if is_page_number(shape):
                        continue
                    body = shape.find("p:txBody", N)
                    if body is None:
                        continue
                    text = text_content(body)
                    prop = shape.find(".//p:cNvPr", N)
                    if prop is not None and prop.get("name") == "supplement-inbox-start" and text.startswith("补充模板\n"):
                        text = text[len("补充模板\n"):].strip()
                    if text:
                        text_items.append(feedback_item(text, number, part, "text_box", shape))
            notes_text = ""
            for target, kind in relationship_map(archive, part).values():
                if kind.endswith("/notesSlide"):
                    notes = E.fromstring(archive.read(target))
                    for shape in notes.findall(".//p:sp", N):
                        ph = shape.find(".//p:ph", N)
                        if ph is not None and ph.get("type") == "body":
                            notes_text = text_content(shape)
            notes_changed = bool(notes_text.strip()) and (number != start or notes_text.strip() != INBOX_NOTES)
            if notes_changed:
                user_notes = notes_text
                if number == start and user_notes.startswith(INBOX_NOTES):
                    user_notes = user_notes[len(INBOX_NOTES):].strip()
                if user_notes:
                    text_items.append(feedback_item(user_notes, number, part, "speaker_notes"))
            if nodes or notes_changed:
                pending.append({"page": number, "objects": len(nodes), "notes_added": notes_changed, "hidden": slide.get("show") == "0"})
        processed = set()
        pending_suggestions = set()
        for item in text_items:
            record = (records or {}).get(item["suggestion_id"], {})
            if record.get("content_hash") == item["content_hash"]:
                item["processing_status"] = record.get("status", "unprocessed")
                item["processing_summary"] = record.get("summary", "")
                item["rule_files"] = record.get("rule_files", [])
            else:
                item["processing_status"] = "unprocessed"
            if item["processing_status"] in RESOLVED_STATUSES:
                processed.add(item["suggestion_id"])
            elif item["marked_suggestion"]:
                pending_suggestions.add(item["suggestion_id"])
        return {"slide_count": len(slides), "inbox_marker_count": 1, "inbox_start_page": start,
                "pending_pages": pending, "needs_reconciliation": False,
                "inbox_text_items": text_items,
                "pending_suggestion_ids": sorted(pending_suggestions),
                "processed_suggestion_ids": sorted(processed),
                "pending_feedback_cleanup_ids": sorted(processed)}

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
    result.update(inspect_catalog(selected, read_history(skill_root)["records"]))
    result["ready_for_use"] = not (conflict or result["needs_sync"] or result["needs_reconciliation"] or result["pending_pages"])
    return result


def record_suggestions(skill_root: Path, state: dict, identifiers: list[str],
                       status: str, summary: str | None, rule_files: list[str],
                       expected_sha256: str | None) -> list[str]:
    """Record an agent-reviewed resolution; never modify rules or slides here."""
    if state["copy_conflict"]:
        raise ValueError("参考副本存在独立修改，请先比较合并")
    if status not in RESOLVED_STATUSES | {"needs_clarification"}:
        raise ValueError("建议处理状态无效")
    catalog = Path(state["catalog_path"])
    if not expected_sha256 or state["catalog_sha256"] != expected_sha256 or sha256(catalog) != expected_sha256:
        raise ValueError("参考文件已改变，请重新读取建议后再记录")
    if not summary or not summary.strip():
        raise ValueError("处理建议时需提供明确的处理结果")
    if status == "applied" and not rule_files:
        raise ValueError("应用建议时需列出已更新的规则文件")
    rules = []
    for value in rule_files:
        candidate = skill_root / value
        if Path(value).is_absolute() or not candidate.resolve().is_relative_to(skill_root.resolve()) or not candidate.is_file():
            raise ValueError("规则文件需指向本技能内的现有文件")
        rules.append(candidate.resolve().relative_to(skill_root.resolve()).as_posix())
    items = {item["suggestion_id"]: item for item in state.get("inbox_text_items", [])}
    if any(identifier not in items for identifier in identifiers):
        raise ValueError("本次检查中找不到指定建议，请重新读取")
    history = read_history(skill_root)
    for identifier in dict.fromkeys(identifiers):
        item = items[identifier]
        history["records"][identifier] = {
            "content_hash": item["content_hash"], "text": item["text"],
            "normalized_text": item["normalized_text"], "status": status,
            "summary": summary.strip(), "rule_files": sorted(set(rules)),
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "source": {key: item[key] for key in ("page", "slide_part", "source", "shape_id", "shape_name")},
        }
    path = history_path(skill_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent,
                                         prefix="suggestion-history-", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(history, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        temporary.replace(path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return list(dict.fromkeys(identifiers))

def main() -> None:
    """Print a read-only inventory; status 2 means classification or reconciliation is needed."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--working-copy", type=Path)
    parser.add_argument("--record-suggestion", action="append", default=[], metavar="ID")
    parser.add_argument("--status", choices=("applied", "already_covered", "needs_clarification", "not_applicable"))
    parser.add_argument("--summary")
    parser.add_argument("--rule-file", action="append", default=[])
    parser.add_argument("--expected-catalog-sha256")
    args = parser.parse_args()
    try:
        result = inspect_state(args.skill_root, args.working_copy)
        if args.record_suggestion:
            if args.status is None:
                raise ValueError("记录建议时需指定处理状态")
            identifiers = record_suggestions(args.skill_root, result, args.record_suggestion,
                                              args.status, args.summary, args.rule_file,
                                              args.expected_catalog_sha256)
            result = inspect_state(args.skill_root, args.working_copy)
            result["recorded_suggestion_ids"] = identifiers
    except (OSError, BadZipFile, E.ParseError, KeyError, ValueError) as error:
        print(json.dumps({"ready_for_use": False, "error": str(error)}, ensure_ascii=False))
        sys.exit(1)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["ready_for_use"] or args.record_suggestion else 2)

if __name__ == "__main__":
    main()
