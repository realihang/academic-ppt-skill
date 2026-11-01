"""Refresh native current/total slide numbers in the Academic PPT style."""
from __future__ import annotations

import argparse
from collections.abc import Mapping
import json
from pathlib import Path
import posixpath
from uuid import NAMESPACE_URL, uuid5
from zipfile import ZIP_DEFLATED, ZipFile

from lxml import etree as ET

P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
NS = {'p': P, 'a': A, 'r': R}
PX = 9525
BLUE = '084B99'
WHITE = 'FFFFFF'
NUMBER_NAME = 'academic-page-number'


def xml(root: ET._Element) -> bytes:
    """Serialize an Office part without changing its namespace mapping."""
    return ET.tostring(root, encoding='utf-8', xml_declaration=True, standalone=True)


def target_of(part: str, target: str) -> str:
    """Resolve an internal relationship target."""
    return target.lstrip('/') if target.startswith('/') else posixpath.normpath(
        posixpath.join(posixpath.dirname(part), target)
    )


def relations(data: Mapping[str, bytes], part: str) -> dict[str, tuple[str, str]]:
    """Read internal relationships for a package part."""
    folder, filename = posixpath.split(part)
    name = posixpath.join(folder, '_rels', filename + '.rels')
    if name not in data:
        return {}
    return {
        node.get('Id', ''): (node.get('Type', '').rsplit('/', 1)[-1],
                              target_of(part, node.get('Target', '')))
        for node in ET.fromstring(data[name]) if node.get('TargetMode') != 'External'
    }


def ordered_slides(data: Mapping[str, bytes]) -> list[str]:
    """Return slide parts in presentation order, including hidden slides."""
    root = ET.fromstring(data['ppt/presentation.xml'])
    rels = relations(data, 'ppt/presentation.xml')
    return [rels[node.get(f'{{{R}}}id')][1]
            for node in root.findall('p:sldIdLst/p:sldId', NS)]


def bounds(shape: ET._Element) -> tuple[float, float, float, float] | None:
    """Return an ungrouped shape rectangle in EMU when it is explicit."""
    xf = shape.find('p:spPr/a:xfrm', NS)
    if xf is None:
        return None
    off, ext = xf.find('a:off', NS), xf.find('a:ext', NS)
    if off is None or ext is None:
        return None
    return float(off.get('x', '0')), float(off.get('y', '0')), float(ext.get('cx', '0')), float(ext.get('cy', '0'))


def fill_color(parent: ET._Element | None, theme: Mapping[str, str]) -> str | None:
    """Resolve a common explicit solid fill; images need visual review."""
    if parent is None:
        return None
    fill = parent.find('a:solidFill', NS)
    if fill is None or len(fill) == 0:
        return None
    node = fill[0]
    value = node.get('val')
    if ET.QName(node).localname == 'schemeClr':
        value = theme.get(value or '')
    elif ET.QName(node).localname == 'sysClr':
        value = node.get('lastClr')
    alpha = node.find('a:alpha', NS)
    if alpha is not None and int(alpha.get('val', '100000')) < 90000:
        return None
    return value.upper() if value and len(value) == 6 else None


def shape_colors_at(root: ET._Element, x: float, y: float,
                    theme: Mapping[str, str]) -> list[str]:
    """Collect opaque native fills beneath a point, including grouped shapes."""
    result: list[str] = []

    def walk(container: ET._Element, sx: float, sy: float,
             dx: float, dy: float) -> None:
        for node in container:
            if node.tag == f'{{{P}}}grpSp':
                xf = node.find('p:grpSpPr/a:xfrm', NS)
                if xf is None:
                    continue
                off, ext = xf.find('a:off', NS), xf.find('a:ext', NS)
                child_off, child_ext = xf.find('a:chOff', NS), xf.find('a:chExt', NS)
                if any(item is None for item in (off, ext, child_off, child_ext)):
                    continue
                gsx = float(ext.get('cx', '0')) / max(1, float(child_ext.get('cx', '1')))
                gsy = float(ext.get('cy', '0')) / max(1, float(child_ext.get('cy', '1')))
                walk(node, sx * gsx, sy * gsy,
                     dx + sx * (float(off.get('x', '0')) - gsx * float(child_off.get('x', '0'))),
                     dy + sy * (float(off.get('y', '0')) - gsy * float(child_off.get('y', '0'))))
                continue
            box = bounds(node)
            if box is None:
                continue
            left, top, width, height = box
            if dx + sx * left <= x <= dx + sx * (left + width) and dy + sy * top <= y <= dy + sy * (top + height):
                color = fill_color(node.find('p:spPr', NS), theme)
                if color:
                    result.append(color)

    tree = root.find('p:cSld/p:spTree', NS)
    if tree is not None:
        walk(tree, 1, 1, 0, 0)
    return result


def page_color(data: Mapping[str, bytes], part: str,
               width: int, theme: Mapping[str, str]) -> str:
    """Choose blue on light backgrounds and white on dark native backgrounds."""
    chain = [part]
    while len(chain) < 3:
        if chain[-1].startswith('ppt/slides/'):
            kind = 'slideLayout'
        elif chain[-1].startswith('ppt/slideLayouts/'):
            kind = 'slideMaster'
        else:
            break
        parent = next((target for rel_kind, target in relations(data, chain[-1]).values() if rel_kind == kind), None)
        if parent is None:
            break
        chain.append(parent)
    background = WHITE
    roots = [ET.fromstring(data[name]) for name in reversed(chain)]
    for root in roots:
        color = fill_color(root.find('p:cSld/p:bg/p:bgPr', NS), theme)
        if color:
            background = color
    x, y = width - 108 * PX, 45 * PX
    for root in roots:
        colors = shape_colors_at(root, x, y, theme)
        if colors:
            background = colors[-1]
    rgb = [int(background[start:start + 2], 16) / 255 for start in (0, 2, 4)]
    linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in rgb]
    luminance = sum(v * weight for v, weight in zip(linear, (0.2126, 0.7152, 0.0722)))
    return WHITE if luminance < 0.35 else BLUE


def paragraph_properties(parent: ET._Element) -> None:
    """Set 1.2 line spacing, no bullets and no paragraph gaps."""
    spacing = ET.SubElement(parent, f'{{{A}}}lnSpc')
    ET.SubElement(spacing, f'{{{A}}}spcPct', val='120000')
    for tag in ('spcBef', 'spcAft'):
        ET.SubElement(ET.SubElement(parent, f'{{{A}}}{tag}'), f'{{{A}}}spcPts', val='0')
    ET.SubElement(parent, f'{{{A}}}buNone')


def run_properties(parent: ET._Element, tag: str, color: str) -> ET._Element:
    """Use Arial 20 pt for all page-number characters."""
    node = ET.SubElement(parent, f'{{{A}}}{tag}', lang='en-US', sz='2000', b='0', dirty='0')
    ET.SubElement(ET.SubElement(node, f'{{{A}}}solidFill'), f'{{{A}}}srgbClr', val=color)
    for font_tag in ('latin', 'ea', 'cs'):
        ET.SubElement(node, f'{{{A}}}{font_tag}', typeface='Arial')
    return node


def number_shape(shape_id: int, width: int, current: int,
                 total: int, color: str, identity: str) -> ET._Element:
    """Make an editable native slide-number field and a total-count suffix."""
    shape = ET.Element(f'{{{P}}}sp')
    nv = ET.SubElement(shape, f'{{{P}}}nvSpPr')
    ET.SubElement(nv, f'{{{P}}}cNvPr', id=str(shape_id), name=NUMBER_NAME)
    ET.SubElement(nv, f'{{{P}}}cNvSpPr')
    ET.SubElement(ET.SubElement(nv, f'{{{P}}}nvPr'), f'{{{P}}}ph', type='sldNum', sz='quarter', idx='4')
    props = ET.SubElement(shape, f'{{{P}}}spPr')
    xf = ET.SubElement(props, f'{{{A}}}xfrm')
    ET.SubElement(xf, f'{{{A}}}off', x=str(width - 172 * PX), y=str(27 * PX))
    ET.SubElement(xf, f'{{{A}}}ext', cx=str(128 * PX), cy=str(36 * PX))
    ET.SubElement(ET.SubElement(props, f'{{{A}}}prstGeom', prst='rect'), f'{{{A}}}avLst')
    ET.SubElement(props, f'{{{A}}}noFill')
    ET.SubElement(ET.SubElement(props, f'{{{A}}}ln'), f'{{{A}}}noFill')
    body = ET.SubElement(shape, f'{{{P}}}txBody')
    bp = ET.SubElement(body, f'{{{A}}}bodyPr', wrap='none', anchor='ctr', lIns='0', rIns='0', tIns='0', bIns='0')
    ET.SubElement(bp, f'{{{A}}}noAutofit')
    style = ET.SubElement(body, f'{{{A}}}lstStyle')
    paragraph_properties(ET.SubElement(style, f'{{{A}}}defPPr'))
    para = ET.SubElement(body, f'{{{A}}}p')
    paragraph_properties(ET.SubElement(para, f'{{{A}}}pPr', algn='r', marL='0', marR='0', indent='0'))
    field = ET.SubElement(para, f'{{{A}}}fld', id='{' + str(uuid5(NAMESPACE_URL, identity)).upper() + '}', type='slidenum')
    run_properties(field, 'rPr', color)
    ET.SubElement(field, f'{{{A}}}t').text = str(current)
    run = ET.SubElement(para, f'{{{A}}}r')
    run_properties(run, 'rPr', color)
    ET.SubElement(run, f'{{{A}}}t').text = f'/{total}'
    run_properties(para, 'endParaRPr', color)
    return shape


def apply_page_numbers(data: dict[str, bytes]) -> dict[str, object]:
    """Refresh a package in memory, preserving unrelated content and notes."""
    presentation = ET.fromstring(data['ppt/presentation.xml'])
    size = presentation.find('p:sldSz', NS)
    if size is None:
        raise ValueError('PPT缺少页面尺寸')
    width = int(size.get('cx', '0'))
    parts = ordered_slides(data)
    if not parts:
        raise ValueError('PPT没有幻灯片')
    presentation.set('firstSlideNum', '1')
    data['ppt/presentation.xml'] = xml(presentation)
    theme = {'bg1': WHITE, 'bg2': WHITE, 'tx1': '000000', 'accent1': BLUE}
    for name in data:
        if name.startswith('ppt/theme/') and name.endswith('.xml'):
            scheme = ET.fromstring(data[name]).find('a:themeElements/a:clrScheme', NS)
            if scheme is not None:
                for node in scheme:
                    if len(node):
                        theme[ET.QName(node).localname] = node[0].get('val') or node[0].get('lastClr', WHITE)
                break
    all_parts = [name for name in data if name.startswith(('ppt/slideMasters/', 'ppt/slideLayouts/')) and name.endswith('.xml')]
    all_parts.extend(parts)
    colors: dict[str, str] = {}
    for name in all_parts:
        root = ET.fromstring(data[name])
        tree = root.find('p:cSld/p:spTree', NS)
        if tree is None:
            continue
        for shape in list(tree):
            nv = shape.find('p:nvSpPr/p:cNvPr', NS)
            ph = shape.find('p:nvSpPr/p:nvPr/p:ph', NS)
            if (nv is not None and nv.get('name') == NUMBER_NAME) or (ph is not None and ph.get('type') == 'sldNum'):
                tree.remove(shape)
        # Header titles reserve the number area; their text/font remain intact.
        limit = width - 194 * PX
        for shape in tree:
            box = bounds(shape)
            if box is None:
                continue
            left, top, shape_width, height = box
            centered = shape.xpath('.//a:pPr[@algn="ctr" or @algn="r"]', namespaces=NS)
            if not centered and top < 70 * PX and top + height < 130 * PX and left < limit and left + shape_width > limit and shape.find('p:txBody', NS) is not None and shape.xpath('.//a:t[text()]', namespaces=NS):
                extent = shape.find('p:spPr/a:xfrm/a:ext', NS)
                extent.set('cx', str(int(limit - left)))
        shape_id = max((int(node.get('id', '0')) for node in tree.findall('.//p:cNvPr', NS)), default=1) + 1
        is_slide = name in parts
        current = parts.index(name) + 1 if is_slide else 1
        color = page_color(data, name, width, theme)
        tree.append(number_shape(shape_id, width, current, len(parts), color, name))
        if not is_slide:
            hf = root.find('p:hf', NS)
            if hf is None:
                hf = ET.Element(f'{{{P}}}hf')
                before = root.find('p:txStyles', NS)
                if before is None:
                    before = root.find('p:extLst', NS)
                root.insert(root.index(before), hf) if before is not None else root.append(hf)
            hf.set('sldNum', '1')
        data[name] = xml(root)
        if is_slide:
            colors[str(current)] = color
    return {'slide_count': len(parts), 'font': 'Arial', 'font_size_pt': 20,
            'position': 'top_right', 'colors': colors, 'includes_hidden_slides': True}


def refresh(source: Path, output: Path) -> dict[str, object]:
    """Write a new PPTX with refreshed numbers, never overwrite a source."""
    if source.resolve() == output.resolve() or output.exists():
        raise ValueError('请使用新的输出文件名，不能直接覆盖原文件')
    if source.suffix.lower() != '.pptx' or output.suffix.lower() != '.pptx':
        raise ValueError('输入和输出都须为.pptx文件')
    with ZipFile(source) as archive:
        data = {info.filename: archive.read(info.filename) for info in archive.infolist()}
        infos = archive.infolist()
    result = apply_page_numbers(data)
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, 'x', ZIP_DEFLATED) as archive:
        for info in infos:
            archive.writestr(info, data[info.filename])
    result['output'] = str(output.resolve())
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description='刷新右上角Arial 20磅的当前页/总页数。')
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = refresh(args.source, args.output)
    except (OSError, ValueError, KeyError, ET.XMLSyntaxError) as error:
        parser.exit(1, f'{error}\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
