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

def convert_position(position, isHorizontal, type):
    box = Box(position)
    box.IsHorizontal = isHorizontal
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
        lines.append(box)
    else:
        lines.append(convert_position(get_position(element.bbox), True, BorderType.Top))
        lines.append(convert_position(get_position(element.bbox), True, BorderType.Bottom))
        lines.append(convert_position(get_position(element.bbox), False, BorderType.Left))
        lines.append(convert_position(get_position(element.bbox), False, BorderType.Right))
    return lines