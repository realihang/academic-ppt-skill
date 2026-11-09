"""Apply Academic PPT delivery defaults without rebuilding native slides."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import posixpath
from zipfile import BadZipFile

from lxml import etree as ET


P = "http://schemas.openxmlformats.org/presentationml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG = "http://schemas.openxmlformats.org/package/2006/relationships"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"
NS = {"p": P, "a": A}


def xml(root: ET._Element) -> bytes:
    """Serialize a part while retaining its namespace mapping."""
    return ET.tostring(
        root, encoding="utf-8", xml_declaration=True, standalone=True
    )


def set_text_bold(root: ET._Element, bold: bool) -> None:
    """Set explicit text defaults, including newly typed and field text."""
    value = "1" if bold else "0"
    for node in root.xpath(
        ".//a:rPr | .//a:defRPr | .//a:endParaRPr", namespaces=NS
    ):
        node.set("b", value)
    for run in root.xpath(".//a:r | .//a:fld | .//a:br", namespaces=NS):
        props = run.find(f"{{{A}}}rPr")
        if props is None:
            props = ET.Element(f"{{{A}}}rPr")
            run.insert(0, props)
        props.set("b", value)
    for paragraph in root.findall(".//a:p", NS):
        props = paragraph.find(f"{{{A}}}pPr")
        if props is None:
            props = ET.Element(f"{{{A}}}pPr")
            paragraph.insert(0, props)
        default = props.find(f"{{{A}}}defRPr")
        if default is None:
            default = ET.SubElement(props, f"{{{A}}}defRPr")
        default.set("b", value)
        end = paragraph.find(f"{{{A}}}endParaRPr")
        if end is None:
            end = ET.SubElement(paragraph, f"{{{A}}}endParaRPr")
        end.set("b", value)


def body_placeholder(shape: ET._Element) -> ET._Element | None:
    """Identify body containers without confusing body-typed titles."""
    ph = shape.find("p:nvSpPr/p:nvPr/p:ph", NS)
    if ph is None or ph.get("idx") in {"10", "11"}:
        return None
    if ph.get("idx") == "12" or ph.get("type") == "body":
        return ph
    return None


def contains_content(shape: ET._Element) -> bool:
    """Keep real text or embedded content; default editing prompts are empty."""
    if shape.xpath(".//a:blip | .//a:graphic", namespaces=NS):
        return True
    text = "".join(shape.xpath(".//a:t/text()", namespaces=NS)).strip()
    return bool(text) and not text.casefold().startswith(
        ("单击此处编辑", "单击此处添加", "click to edit master", "click to add text")
    )


def cleanup_body_placeholders(data: dict[str, bytes]) -> int:
    """Remove empty slide bodies and shared body boxes no slide uses."""
    roots = {
        name: ET.fromstring(value)
        for name, value in data.items()
        if name.endswith(".xml") and name.startswith(
            ("ppt/slides/", "ppt/slideLayouts/", "ppt/slideMasters/")
        )
    }
    children_by_parent: dict[str, list[str]] = defaultdict(list)
    for child in roots:
        folder, filename = posixpath.split(child)
        relpart = posixpath.join(folder, "_rels", filename + ".rels")
        if relpart not in data:
            continue
        for relation in ET.fromstring(data[relpart]):
            if relation.get("Type") not in {R + "/slideLayout", R + "/slideMaster"}:
                continue
            target = relation.get("Target", "")
            parent = target.lstrip("/") if target.startswith("/") else (
                posixpath.normpath(posixpath.join(folder, target))
            )
            children_by_parent[parent].append(child)
    removed = 0
    for prefix in ("ppt/slides/", "ppt/slideLayouts/", "ppt/slideMasters/"):
        for name, root in roots.items():
            if not name.startswith(prefix):
                continue
            children = children_by_parent[name]
            targets = set(root.xpath(
                ".//p:spTgt/@spid | .//a:stCxn/@id | .//a:endCxn/@id",
                namespaces=NS,
            ))
            for shape in list(root.findall("p:cSld/p:spTree/p:sp", NS)):
                ph = body_placeholder(shape)
                if ph is None:
                    continue
                nv = shape.find("p:nvSpPr/p:cNvPr", NS)
                if nv is not None and nv.get("id") in targets:
                    continue
                if prefix == "ppt/slides/":
                    used = contains_content(shape)
                else:
                    used = any(
                        candidate.get("idx", "0") == ph.get("idx", "0")
                        for child in children
                        for candidate in roots[child].xpath(
                            ".//p:nvPr/p:ph", namespaces=NS
                        )
                    )
                if not used:
                    shape.getparent().remove(shape)
                    removed += 1
            data[name] = xml(root)
    return removed


def set_normal_view(data: dict[str, bytes]) -> None:
    """Persist normal slide view; first-slide selection needs an app check."""
    part = "ppt/viewProps.xml"
    if part in data:
        root = ET.fromstring(data[part])
    else:
        root = ET.Element(f"{{{P}}}viewPr", nsmap={"a": A, "r": R, "p": P})
        normal = ET.SubElement(root, f"{{{P}}}normalViewPr")
        ET.SubElement(normal, f"{{{P}}}restoredLeft", sz="16000")
        ET.SubElement(normal, f"{{{P}}}restoredTop", sz="80000")
    root.set("lastView", "sldView")
    data[part] = xml(root)

    relpart = "ppt/_rels/presentation.xml.rels"
    rels = ET.fromstring(data[relpart])
    if not any(node.get("Type") == R + "/viewProps" for node in rels):
        ids = {node.get("Id") for node in rels}
        rid = "rIdAcademicView"
        while rid in ids:
            rid += "1"
        ET.SubElement(
            rels, f"{{{PKG}}}Relationship", Id=rid,
            Type=R + "/viewProps", Target="viewProps.xml",
        )
        data[relpart] = xml(rels)
    types = ET.fromstring(data["[Content_Types].xml"])
    if not any(node.get("PartName") == "/" + part for node in types):
        ET.SubElement(
            types, f"{{{CT}}}Override", PartName="/" + part,
            ContentType="application/vnd.openxmlformats-officedocument."
                        "presentationml.viewProps+xml",
        )
        data["[Content_Types].xml"] = xml(types)


def apply_delivery_defaults(data: dict[str, bytes]) -> dict[str, object]:
    """Normalize visible editable text and unused default body containers."""
    removed = cleanup_body_placeholders(data)
    for name in list(data):
        if not name.endswith(".xml") or not (
            name == "ppt/presentation.xml" or name.startswith(
                ("ppt/slides/", "ppt/slideLayouts/", "ppt/slideMasters/", "ppt/charts/")
            )
        ):
            continue
        root = ET.fromstring(data[name])
        set_text_bold(root, True)
        for table in root.findall(".//a:tbl", NS):
            for index, row in enumerate(table.findall("a:tr", NS)):
                set_text_bold(row, index == 0)
        for props in root.xpath(
            './/p:cNvPr[starts-with(@name, "table-body-")]', namespaces=NS
        ):
            set_text_bold(props.getparent().getparent(), False)
        data[name] = xml(root)
    set_normal_view(data)
    return {"default_bold": True, "table_body_bold": False,
            "removed_body_placeholders": removed, "last_view": "sldView"}


def finalize(source: Path, output: Path) -> dict[str, object]:
    """Write a separate final package, preserving notes and native parts."""
    from refresh_page_numbers import refresh

    return refresh(source, output)


def main() -> None:
    """Expose the shared final preparation step as a command."""
    parser = argparse.ArgumentParser(description="整理交付PPT的页码、字重、占位框与打开视图")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = finalize(args.source, args.output)
    except (OSError, ValueError, KeyError, BadZipFile, ET.XMLSyntaxError) as error:
        parser.exit(1, f"{error}\n")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
