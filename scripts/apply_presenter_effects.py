"""Add native click-to-reveal fades while keeping editable slide objects."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from zipfile import ZIP_DEFLATED, ZipFile

from lxml import etree as E


P = "http://schemas.openxmlformats.org/presentationml/2006/main"
NS = {"p": P}


def sub(parent: E._Element, local: str, **attributes: str) -> E._Element:
    return E.SubElement(parent, f"{{{P}}}{local}", **attributes)


def add_presenter_effects(root: E._Element, duration: int = 350, replace_existing: bool = False) -> dict[str, object]:
    """Use reveal-N names as click batches; unmarked objects stay visible."""
    if not 100 <= duration <= 2000:
        raise ValueError("动画时长须在100至2000毫秒之间")
    if root.find("p:timing", NS) is not None and not replace_existing:
        raise ValueError("页面已有动画。统一动效时请显式使用--replace-existing")
    for local in ("transition", "timing"):
        old = root.find(f"p:{local}", NS)
        if old is not None:
            root.remove(old)
    batches: dict[int, list[tuple[str, str]]] = {}
    for node in root.findall("p:cSld/p:spTree/*", NS):
        props = node.find(".//p:cNvPr", NS)
        if props is None:
            continue
        found = re.match(r"reveal-(\d+)(?:-|$)", props.get("name", ""))
        if found:
            batches.setdefault(int(found.group(1)), []).append((props.get("id"), E.QName(node).localname))
    if not batches:
        return {"clicks": 0, "targets": []}
    timing = E.Element(f"{{{P}}}timing")
    tn_list = sub(timing, "tnLst")
    main_root = sub(sub(tn_list, "par"), "cTn", id="1", dur="indefinite", restart="never", nodeType="tmRoot")
    sequence = sub(sub(main_root, "childTnLst"), "seq", concurrent="1", nextAc="seek")
    main_sequence = sub(sequence, "cTn", id="2", dur="indefinite", nodeType="mainSeq")
    children = sub(main_sequence, "childTnLst")
    build_list = E.Element(f"{{{P}}}bldLst")
    next_id = 3
    targets: list[str] = []

    def common(parent: E._Element, **values: str) -> E._Element:
        nonlocal next_id
        node = sub(parent, "cTn", id=str(next_id), **values)
        next_id += 1
        return node

    for group, entries in enumerate(value for _, value in sorted(batches.items())):
        click_container = common(sub(children, "par"), fill="hold")
        sub(sub(click_container, "stCondLst"), "cond", delay="indefinite")
        start_container = common(sub(sub(click_container, "childTnLst"), "par"), fill="hold")
        sub(sub(start_container, "stCondLst"), "cond", delay="0")
        effects = sub(start_container, "childTnLst")
        for entry_index, (shape_id, kind) in enumerate(entries):
            targets.append(shape_id)
            effect = common(sub(effects, "par"), presetID="10", presetClass="entr", presetSubtype="0", fill="hold", grpId=str(group), nodeType="clickEffect" if entry_index == 0 else "withEffect")
            sub(sub(effect, "stCondLst"), "cond", delay="0")
            behaviors = sub(effect, "childTnLst")
            show = sub(behaviors, "set")
            behavior = sub(show, "cBhvr")
            show_time = common(behavior, dur="1", fill="hold")
            sub(sub(show_time, "stCondLst"), "cond", delay="0")
            sub(sub(behavior, "tgtEl"), "spTgt", spid=shape_id)
            sub(sub(behavior, "attrNameLst"), "attrName").text = "style.visibility"
            sub(sub(show, "to"), "strVal", val="visible")
            fade_behavior = sub(sub(behaviors, "animEffect", transition="in", filter="fade"), "cBhvr")
            common(fade_behavior, dur=str(duration))
            sub(sub(fade_behavior, "tgtEl"), "spTgt", spid=shape_id)
            if kind == "sp":
                sub(build_list, "bldP", spid=shape_id, grpId=str(group))
            else:
                graphic = sub(build_list, "bldGraphic", spid=shape_id, grpId=str(group))
                sub(graphic, "bldAsOne")
    for name, event in (("prevCondLst", "onPrev"), ("nextCondLst", "onNext")):
        condition = sub(sub(sequence, name), "cond", evt=event, delay="0")
        sub(sub(condition, "tgtEl"), "sldTgt")
    if len(build_list):
        timing.append(build_list)
    position = next(
        (i for i, node in enumerate(root) if E.QName(node).localname == "extLst"),
        len(root),
    )
    root.insert(position, timing)
    ids = root.xpath(".//p:cTn/@id", namespaces=NS)
    assert len(ids) == len(set(ids)), "动画时间节点编号重复"
    available = set(root.xpath("p:cSld/p:spTree//p:cNvPr/@id", namespaces=NS))
    assert set(targets) <= available, "动画引用的图形不存在"
    return {"clicks": len(batches), "targets": targets}


def apply(source: Path, output: Path, duration: int, replace_existing: bool = False) -> dict[str, object]:
    if source.resolve() == output.resolve() or output.exists():
        raise FileExistsError("请使用新的输出文件名，保留原始PPT")
    with ZipFile(source) as archive:
        package = {name: archive.read(name) for name in archive.namelist()}
    report: dict[str, object] = {}
    for name, data in list(package.items()):
        if name.startswith("ppt/slides/") and name.endswith(".xml"):
            root = E.fromstring(data)
            report[name] = add_presenter_effects(root, duration, replace_existing)
            package[name] = E.tostring(root, encoding="utf-8", xml_declaration=True, standalone=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "x", ZIP_DEFLATED) as archive:
        for name, data in package.items():
            archive.writestr(name, data)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="对标记为reveal-N的原生对象添加分组点击淡入")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--duration", type=int, default=350)
    parser.add_argument("--replace-existing", action="store_true")
    args = parser.parse_args()
    print(json.dumps(apply(args.source, args.output, args.duration, args.replace_existing), ensure_ascii=False))


if __name__ == "__main__":
    main()
