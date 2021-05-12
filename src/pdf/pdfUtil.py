from functools import reduce
from models.Position import Position
from models.Box import Box
from models.BorderType import BorderType

_lineDelta = 1.75

def get_acro_key(annotation):
    keys = []
    keyNode = annotation['/T']
    if keyNode != None:
        keys.append(keyNode[1:-1])
    parent = annotation['/Parent']
    while parent != None:
        parentKeyNode = parent['/T']
        if parentKeyNode != None:
            keys.append(parentKeyNode[1:-1])
        parent = parent['/Parent']
    return reduce((lambda x, y: y + "." + x), keys)

def get_position(bbox):
    return Position(bbox[0], bbox[2], bbox[3], bbox[1])

def convert_position(element, isHorizontal, type):
    position = get_position(element.bbox)
    box = Box(position)
    box.IsHorizontal = isHorizontal
    box.LineWidth = element.linewidth
    if isHorizontal:
        if type == BorderType.Top:
            position.Bottom = position.Top
        else:
            position.Top = position.Bottom
    else:
        if type == BorderType.Left:
            position.Right = position.Left
        else:
            position.Left = position.Right
    return box

def find_lines(element):
    lines = []
    pos = get_position(element.bbox)
    if pos.Top - pos.Bottom < _lineDelta or pos.Right - pos.Left < _lineDelta:
        box = Box(pos)
        box.IsHorizontal = abs(pos.Top - pos.Bottom) < _lineDelta and abs(pos.Right - pos.Left) > _lineDelta
        box.LineWidth = element.linewidth
        lines.append(box)
    else:
        lines.append(convert_position(element, True, BorderType.Top))
        lines.append(convert_position(element, True, BorderType.Bottom))
        lines.append(convert_position(element, False, BorderType.Left))
        lines.append(convert_position(element, False, BorderType.Right))
    return lines

def merge_lines(lines):
    # merge horizontal lines
    ypos = set()
    for line in [x for x in lines if x.IsHorizontal]:
        ypos.add(line.Position.Bottom)
    for yposition in ypos:
        xlines = sorted([x for x in [x for x in lines if x.IsHorizontal] if abs(x.Position.Bottom - yposition) < _lineDelta], key=lambda x: x.Position.Left)
        i = 0
        while i < len(xlines):
            line = xlines[i]
            overlap = [x for x in xlines if xlines.index(x) > i and x.Position.Left - line.Position.Right < _lineDelta]
            if len(overlap) > 0:
                line.Position.Right = max(line.Position.Right, max(x.Position.Right for x in overlap))
                for x in overlap:
                    xlines.remove(x)
                    lines.remove(x)
                continue
            i += 1

    # merge vertical lines
    xpos = set()
    for line in [x for x in lines if not x.IsHorizontal]:
        xpos.add(line.Position.Right)
    for xposition in xpos:
        ylines = sorted([x for x in [x for x in lines if not x.IsHorizontal] if abs(x.Position.Right - xposition) < _lineDelta], key=lambda x: x.Position.Top, reverse=True)
        i = 0
        while i < len(ylines):
            line = ylines[i]
            overlap = [x for x in ylines if ylines.index(x) > i and x.Position.Top >= line.Position.Bottom - _lineDelta]
            if len(overlap) > 0:
                line.Position.Bottom = min(line.Position.Bottom, min(x.Position.Bottom for x in overlap))
                for x in overlap:
                    ylines.remove(x)
                    lines.remove(x)
                continue
            i += 1