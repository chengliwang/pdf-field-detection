from functools import reduce
from models.Position import Position
from models.Box import Box
from models.BorderType import BorderType
from models.ElementType import ElementType
import re

_lineDelta = 1.75
_fieldHeight = 12.5
_combLineWidthDelta = 6.5
_maxCombLineWidth = 20
_centLinePercentage = 0.3
_maxCentLineWidth = 35
_maxFieldWidth = 110
_textToIgnore = "00|SP|-|,|IC0001|NP|RC|RZ|AMJ"

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

def split_lines(lines):
    # split horizontal lines
    for line in sorted([x for x in lines if x.IsHorizontal], key=lambda x: x.Position.Bottom, reverse=True):

        # find intersecting vertical lines
        vInterLines = sorted([x for x in [x for x in lines if not x.IsHorizontal] \
            if x.Position.Top > line.Position.Top + _lineDelta and \
               x.Position.Bottom <= line.Position.Bottom + _lineDelta and \
               x.Position.Left > line.Position.Left + _lineDelta and \
               x.Position.Right < line.Position.Right - _lineDelta \
            ], key=lambda x: x.Position.Left) 

        # remove comb and cent lines          
        if len(vInterLines) > 0:
            x1 = line.Position.Left
            i = 0
            while i < len(vInterLines):
                x2 = vInterLines[i].Position.Left
                x3 = line.Position.Right
                if i + 1 < len(vInterLines):
                    x3 = vInterLines[i + 1].Position.Left
                width1 = x2 - x1
                width2 = x3 - x2
                isComboLine = abs(width1 - width2) < _combLineWidthDelta and width1 <= _maxCombLineWidth and width1 <= _maxCombLineWidth
                isCentLine = not isComboLine and width2 < _maxCentLineWidth and width2 / (width1 + width2) <= _centLinePercentage and \
                    width1 + width2 < _maxFieldWidth
                x1 = x2
                if isCentLine or isComboLine:
                    vInterLines.pop(i)                                     
                    continue
                i += 1  

        # split lines          
        if len(vInterLines) > 0:
            x1 = line.Position.Left
            i = 0
            while i < len(vInterLines):
                x2 = vInterLines[i].Position.Left
                box = Box(Position(x1, x2, line.Position.Top, line.Position.Bottom))
                box.IsHorizontal = True
                box.LineWidth = line.LineWidth
                lines.append(box)
                x1 = x2
                i += 1
            box = Box(Position(x1, line.Position.Right, line.Position.Top, line.Position.Bottom))
            box.IsHorizontal = True
            box.LineWidth = line.LineWidth
            lines.append(box)
            lines.remove(line)

def find_text(left, right, top, bottom, textLines):
    return [x for x in textLines if left <= x.Position.Right and right >= x.Position.Left and top >= x.Position.Bottom and bottom <= x.Position.Top]

def ignoreText(text):
    strippedText = text.replace(" ", "").replace("\"", "")
    return re.match("^" + _textToIgnore + "$", strippedText) != None

def extract_line_features(lines, textLines, pageHeight):
    for line in sorted([x for x in lines if x.IsHorizontal], key=lambda x: x.Position.Bottom, reverse=True):
        
        # find intersecting vertical lines
        vInterLines = sorted([x for x in [x for x in lines if not x.IsHorizontal] \
            if x.Position.Top > line.Position.Top + _lineDelta and \
               x.Position.Bottom <= line.Position.Bottom + _lineDelta and \
               x.Position.Left >= line.Position.Left - _lineDelta and \
               x.Position.Right <= line.Position.Right + _lineDelta \
            ], key=lambda x: x.Position.Left)

        # find left and right borders
        borders = []
        if len(vInterLines) > 0:
            if abs(vInterLines[0].Position.Left - line.Position.Left) <= _lineDelta:
                borders.append(vInterLines[0])
            if abs(vInterLines[len(vInterLines) - 1].Position.Right - line.Position.Right) <= _lineDelta:
                borders.append(vInterLines[len(vInterLines) - 1])
        for border in borders:
            vInterLines.remove(border)
        
        # find lines above
        linesAbove = [x for x in lines if x.IsHorizontal and x.Position.Bottom > line.Position.Top and \
            (x.Position.Left >= line.Position.Left - _lineDelta and x.Position.Left < line.Position.Right or
             x.Position.Right <= line.Position.Right + _lineDelta and x.Position.Right > line.Position.Left or
             x.Position.Left < line.Position.Left + _lineDelta and x.Position.Right > line.Position.Right - _lineDelta)]
        top = pageHeight
        if len(linesAbove) > 0:
            top = min(x.Position.Bottom for x in linesAbove)        

        # find comb and cent lines
        if len(vInterLines) > 0:
            line.HasComboLine = len(vInterLines) > 1
            if (len(vInterLines) == 1):
                width1 = vInterLines[0].Position.Left - line.Position.Left
                width2 = line.Position.Right - vInterLines[0].Position.Right
                line.HasCentLine = width2 < _maxCentLineWidth and width2 / (width1 + width2) <= _centLinePercentage and width1 + width2 < _maxFieldWidth

        # find top boundary
        line.FieldPosition = Position(line.Position.Left, line.Position.Right, line.Position.Top, line.Position.Bottom)
        if len(borders) > 0:
            top = max(x.Position.Top for x in borders)
            line.TopElement = ElementType.Border            
            if len(linesAbove) > 0:
                lineAbove = min(x.Position.Bottom for x in linesAbove)
                top = min(lineAbove, top)
                if lineAbove <= top:
                    line.TopElement = ElementType.Line
        elif len(linesAbove) > 0:
            top = min(x.Position.Bottom for x in linesAbove)
            line.TopElement = ElementType.Line
        elif len(vInterLines) > 0:
            top = max(x.Position.Bottom for x in vInterLines)
            line.TopElement = ElementType.CombOrCent
        line.FieldPosition.Top = top

        # find texts above
        textsAbove = find_text(line.Position.Left, line.Position.Right, top, line.Position.Bottom, textLines)
        if len(textsAbove) > 0:
            lastLine = [x for x in textsAbove if abs(x.Position.Bottom - min(x.Position.Bottom for x in textsAbove)) <= _lineDelta]
            lastLineText = ""
            for x in lastLine:
                lastLineText += x.Text
            if not ignoreText(lastLineText):
                leftText = [x for x in textsAbove if x.Position.Bottom <= line.Position.Bottom + _fieldHeight and \
                    x.Position.Right - line.Position.Left < 10]
                if len(leftText) > 0:
                    line.LeftPadding = max(x.Position.Right for x in leftText) - line.Position.Left
                    line.FieldPosition.Left = line.Position.Left + line.LeftPadding
                rightText = [x for x in textsAbove if x.Position.Bottom <= line.Position.Bottom + _fieldHeight and \
                    line.Position.Right - x.Position.Left < 10]
                if len(rightText) > 0:
                    line.RightPadding = line.Position.Right - min(x.Position.Left for x in rightText)
                    line.FieldPosition.Right = line.Position.Right - line.RightPadding
                remainingText = list(set(textsAbove)-set(leftText)-set(rightText))
                if len(remainingText) > 0:
                    line.TopElement = ElementType.Text
                    line.FieldPosition.Top = max(line.Position.Top, min(x.Position.Bottom for x in remainingText))

        