"""Select/repeat reference slides while retaining native layouts and masters."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import posixpath
from zipfile import ZIP_DEFLATED, ZipFile

from lxml import etree as ET

from refresh_page_numbers import apply_page_numbers


P = "http://schemas.openxmlformats.org/presentationml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG = "http://schemas.openxmlformats.org/package/2006/relationships"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"


def xml(root: ET._Element) -> bytes:
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def rel_file(part: str) -> str:
    folder, filename = posixpath.split(part)
    return posixpath.join(folder, "_rels", filename + ".rels")


def target_of(part: str, target: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    return posixpath.normpath(posixpath.join(posixpath.dirname(part), target))


def selected_pages(value: str, count: int) -> list[int]:
    try:
        result = [int(item.strip()) for item in value.split(",")]
    except ValueError as error:
        raise ValueError("页码请用逗号分隔，例如1,2,6,7") from error
    if not result or any(page < 1 or page > count for page in result):
        raise ValueError(f"页码必须在1至{count}之间")
    if len(result) > 200:
        raise ValueError("单次最多复制200页")
    return result


def clone_slides(reference: Path, output: Path, value: str) -> dict[str, object]:
    if reference.resolve() == output.resolve():
        raise ValueError("输出路径不能覆盖参考文件")
    if output.exists():
        raise FileExistsError(f"输出已存在，请使用新文件名：{output}")
    if output.suffix.lower() != ".pptx":
        raise ValueError("输出文件需要以.pptx结尾")
    with ZipFile(reference) as archive:
        data = {name: archive.read(name) for name in archive.namelist()}
    original = dict(data)
    presentation = ET.fromstring(data["ppt/presentation.xml"])
    rels = ET.fromstring(data["ppt/_rels/presentation.xml.rels"])
    slide_list = presentation.find(f"{{{P}}}sldIdLst")
    if slide_list is None:
        raise ValueError("参考文件没有幻灯片列表")
    relations = {relation.get("Id"): relation for relation in rels}
    slides = [
        target_of(
            "ppt/presentation.xml",
            relations[slide.get(f"{{{R}}}id")].get("Target", ""),
        )
        for slide in slide_list
    ]
    pages = selected_pages(value, len(slides))
    ctypes = ET.fromstring(data["[Content_Types].xml"])
    overrides = {
        node.get("PartName", "").lstrip("/"): node.get("ContentType", "")
        for node in ctypes if node.get("PartName")
    }
    for relation in list(rels):
        if relation.get("Type") == R + "/slide":
            rels.remove(relation)
    slide_list.clear()

    for index, page in enumerate(pages, 1):
        old = slides[page - 1]
        new = f"ppt/slides/skillSlide{index}.xml"
        data[new] = original[old]
        overrides[new] = overrides[old]
        new_rels = ET.fromstring(original[rel_file(old)])
        for relation in new_rels:
            if relation.get("TargetMode") == "External":
                continue
            target = target_of(old, relation.get("Target", ""))
            if relation.get("Type") == R + "/notesSlide":
                new_note = f"ppt/notesSlides/skillNotes{index}.xml"
                data[new_note] = original[target]
                overrides[new_note] = overrides[target]
                note_rels = ET.fromstring(original[rel_file(target)])
                for note_relation in note_rels:
                    if note_relation.get("TargetMode") == "External":
                        continue
                    note_target = (
                        new if note_relation.get("Type") == R + "/slide"
                        else target_of(target, note_relation.get("Target", ""))
                    )
                    note_relation.set("Target", posixpath.relpath(note_target, posixpath.dirname(new_note)))
                data[rel_file(new_note)] = xml(note_rels)
                target = new_note
            relation.set("Target", posixpath.relpath(target, posixpath.dirname(new)))
        data[rel_file(new)] = xml(new_rels)
        rid = f"rIdSkillSlide{index}"
        ET.SubElement(
            rels, f"{{{PKG}}}Relationship", Id=rid,
            Type=R + "/slide", Target=posixpath.relpath(new, "ppt"),
        )
        ET.SubElement(
            slide_list, f"{{{P}}}sldId",
            {"id": str(255 + index), f"{{{R}}}id": rid},
        )

    data["ppt/presentation.xml"] = xml(presentation)
    data["ppt/_rels/presentation.xml.rels"] = xml(rels)
    if "docProps/app.xml" in data:
        app = ET.fromstring(data["docProps/app.xml"])
        for node in app.iter():
            if node.tag.endswith("}Slides"):
                node.text = str(len(pages))
        data["docProps/app.xml"] = xml(app)

    apply_page_numbers(data)

    # Prune inactive sample slides and notes by following the package graph.
    keep: set[str] = set()

    def visit(part: str) -> None:
        if part in keep:
            return
        if part:
            if part not in data:
                raise ValueError(f"内部资源缺失：{part}")
            keep.add(part)
        relation_file = rel_file(part) if part else "_rels/.rels"
        if relation_file not in data:
            return
        keep.add(relation_file)
        for relation in ET.fromstring(data[relation_file]):
            if relation.get("TargetMode") != "External":
                visit(target_of(part, relation.get("Target", "")))

    visit("")
    for node in list(ctypes):
        if node.get("PartName"):
            ctypes.remove(node)
    for name in sorted(keep):
        if name in overrides:
            ET.SubElement(
                ctypes, f"{{{CT}}}Override",
                PartName="/" + name, ContentType=overrides[name],
            )
    data["[Content_Types].xml"] = xml(ctypes)
    keep.add("[Content_Types].xml")
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "x", ZIP_DEFLATED) as archive:
        for name in sorted(keep):
            archive.writestr(name, data[name])
    return {
        "output": str(output.resolve()),
        "slide_count": len(pages),
        "reference_pages": pages,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="按页码复制融合参考PPT，保留原生母版。")
    parser.add_argument(
        "--reference", type=Path,
        default=None,
    )
    parser.add_argument(
        "--aspect-ratio", choices=("16:9", "4:3"), default="16:9",
        help="默认16:9，可选4:3",
    )
    parser.add_argument("--slides", required=True, help="1开始的页码，逗号分隔；允许重复")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        filename = (
            "reference-4x3.pptx" if args.aspect_ratio == "4:3" else "reference.pptx"
        )
        reference = args.reference or (
            Path(__file__).resolve().parents[1] / "assets" / filename
        )
        result = clone_slides(reference, args.output, args.slides)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"{error}\n")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
