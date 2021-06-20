from functools import reduce
from pdf.models.Position import Position
from pdf.models.Box import Box
from pdf.models.BorderType import BorderType
from pdf.models.ElementType import ElementType
import re, os, csv
import tempfile
from pdfrw import PdfWriter, PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.colors import transparent
from PyPDF2 import PdfFileReader, PdfFileWriter
from PyPDF2.generic import NameObject

_lineDelta = 1.75
_fieldHeight = 12.5
_maxFieldHeight = 16
_combLineWidthDelta = 6.5
_maxCombLineWidth = 20
_centLinePercentage = 0.3
_maxCentLineWidth = 35
_maxFieldWidth = 110
_textToIgnore = "00|SP|-|,|IC0001|NP|RC|RZ|AMJ|\."
_prefixGap = 10
_suffixGap = 10

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
    if len(keys) > 0:
        return reduce((lambda x, y: y + "." + x), keys)
    return ""

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

        # find comb and cent lines
        if len(vInterLines) > 0:
            line.HasComboLine = len(vInterLines) > 1
            if (len(vInterLines) == 1):
                width1 = vInterLines[0].Position.Left - line.Position.Left
                width2 = line.Position.Right - vInterLines[0].Position.Right
                line.HasCentLine = width2 < _maxCentLineWidth and width2 / (width1 + width2) <= _centLinePercentage and width1 + width2 < _maxFieldWidth

        # find top boundary
        line.FieldPosition = Position(line.Position.Left, line.Position.Right, line.Position.Top, line.Position.Bottom)
        top = pageHeight   
        topBorder = lineAbove = vInterLine = -1
        if len(borders) > 0:
            topBorder = max(x.Position.Top for x in borders)
        if len(linesAbove) > 0:
            lineAbove = min(x.Position.Bottom for x in linesAbove)
        if len(vInterLines) > 0:
            vInterLine = max(x.Position.Top for x in vInterLines)
            if vInterLine - line.Position.Top < _fieldHeight:
                vInterLine = line.Position.Top + _fieldHeight
        if lineAbove > 0:
            top = lineAbove
            line.TopElement = ElementType.Line
            if topBorder > 0:
                top = min(topBorder, lineAbove)
                if lineAbove > topBorder:
                    line.TopElement = ElementType.Border
            elif vInterLine > 0:
                top = min(vInterLine, lineAbove)
                if lineAbove > vInterLine:
                    line.TopElement = ElementType.CombOrCent
        elif topBorder > 0:
            top = topBorder
            line.TopElement = ElementType.Border
        elif vInterLine > 0:
            top = vInterLine
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
        
        # find prefix
        prefixTexts = sorted(find_text(line.FieldPosition.Left - _prefixGap, line.FieldPosition.Left, line.FieldPosition.Top, \
             line.FieldPosition.Bottom, textLines), key=lambda x: x.Position.Right, reverse=True)
        if len(prefixTexts) > 0:
            gap = line.FieldPosition.Left - max(x.Position.Left for x in prefixTexts)
            if gap > 0 and gap <= _prefixGap:
                line.PrefixGap = gap
                line.Prefix = prefixTexts[0].Text.replace("\n", "")
        
        # find suffix
        suffixTexts = sorted(find_text(line.FieldPosition.Right, line.FieldPosition.Right + _suffixGap, line.FieldPosition.Top, \
            line.FieldPosition.Bottom, textLines), key=lambda x: x.Position.Left)
        if len(suffixTexts) > 0:
            gap = min(x.Position.Left for x in suffixTexts) - line.FieldPosition.Right
            if gap > 0 and gap <= _suffixGap:
                line.SuffixGap = gap
                line.Suffix = suffixTexts[0].Text.replace("\n", "")

def match_fields(pdf_page, lines, stats):
    margin = 3.5
    acro_fields = []
    for annotation in pdf_page.Annots:
        key = get_acro_key(annotation)
        if key.startswith("field"):
            acro_fields.append(annotation)
    stats[0] += len(acro_fields)
    isLandscape = pdf_page.Rotate == '90'
    if isLandscape:
        page_height = float(pdf_page.MediaBox[2])

    for line in [x for x in lines if x.IsHorizontal]:
        line_left = line.FieldPosition.Left - margin
        line_right = line.FieldPosition.Right + margin
        line_top = line.FieldPosition.Top + margin
        line_bottom = line.FieldPosition.Bottom - margin
        for annotation in acro_fields:
            position = annotation.Rect
            field_left = float(position[0])
            field_right = float(position[2])
            field_top = float(position[3])
            field_bottom = float(position[1])
            if isLandscape:
                field_left = float(position[1])
                field_right = float(position[3])
                field_top = page_height - float(position[0])
                field_bottom = page_height - float(position[2])
            if field_left >= line_left and field_left <= line_right and \
                field_right >= line_left and field_right <= line_right and \
                field_top <= line_top and field_top >= line_bottom and \
                field_bottom <= line_top and field_bottom >= line_bottom:
                line.IsMarkupField = True
                line.FieldCode = get_acro_key(annotation)
                stats[1] += 1
                break

def markup_pdf(markup_data, input_pdf, output_pdf):
    # create the acroform
    temp_form = tempfile.NamedTemporaryFile(delete=False)
    temp_form_name = temp_form.name
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file_name = temp_file.name
    pdf_canvas = canvas.Canvas(temp_form_name)
    form = pdf_canvas.acroForm

    reader = PdfReader(input_pdf)
    count = 0
    for page_num, page in enumerate(reader.pages):
        # remove existing fields
        page.Annots = []

        # create markup fields
        form_width = float(page.MediaBox[2])
        form_height = float(page.MediaBox[3])
        pdf_canvas.setPageSize((form_width, form_height))
        if page.Rotate == '90':
            pdf_canvas.setPageSize((form_height, form_width))
            
        current_page = markup_data[markup_data.PageNum == page_num + 1]
        for i, row in current_page.iterrows():
            if float(row['IsMarkupField']) > 0.5:
                count += 1
                width = float(row['FieldWidth'])
                height = float(row['FieldHeight'])
                form.textfield(name='field' + str(count), x=float(row['FieldLeft']), y=float(row['FieldBottom']), relative=True, \
                    width=width, height=height, borderWidth=0, fontName='Helvetica', fontSize=9, fillColor=transparent)
        pdf_canvas.showPage()        
    pdf_canvas.save()
    PdfWriter(temp_file_name, trailer=reader).write()

    # merge the fields
    pdf_writer = PdfFileWriter()
    pdf_reader = PdfFileReader(temp_file_name)
    form_reader = PdfFileReader(temp_form_name)
    for page in range(pdf_reader.getNumPages()):
        pdf_page = pdf_reader.getPage(page)
        form_page = form_reader.getPage(page)
        rotate = pdf_page.get('/Rotate', 0)
        if rotate != 0:
            form_page.mergeRotatedTranslatedPage(pdf_page, -rotate, pdf_page.mediaBox.getWidth() / 2, pdf_page.mediaBox.getWidth() / 2)
        else:
            form_page.mergePage(pdf_page)
        pdf_writer.addPage(form_page)
    if "/AcroForm" in form_reader.trailer["/Root"]:
        pdf_writer._root_object.update({NameObject("/AcroForm"): form_reader.trailer["/Root"]['/AcroForm']})
    pdf_writer.write(open(output_pdf, 'wb'))

    # clean up
    temp_form.close()
    temp_file.close()
    os.remove(temp_form_name)
    os.remove(temp_file_name)

def save_pdf_pages_tocsv(filename, pages, csv_file_name):
    with open(csv_file_name, mode='w',  newline='') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow(["FileName", "PageNum", "LineLeft", "LineRight", "LineTop", "LineBottom", "LineWidth", \
            "TopElement", "LeftPadding", "RightPadding", "HasCentLine", "HasComboLine", "FieldWidth", "FieldHeight", \
            "Prefix", "PrefixGap", "Suffix", "SuffixGap", "FieldCode", "FieldLeft", "FieldRight", "FieldTop", "FieldBottom", "IsMarkupField"])
        for i, page in enumerate(pages):
            for line in [x for x in page if x.IsHorizontal]:
                csv_writer.writerow([filename, i + 1, line.Position.Left, line.Position.Right, line.Position.Top, line.Position.Bottom, \
                    line.LineWidth, str(line.TopElement).replace("ElementType.",""), line.LeftPadding, line.RightPadding, line.HasCentLine, line.HasComboLine, \
                    line.FieldPosition.Right - line.FieldPosition.Left, line.FieldPosition.Top - line.FieldPosition.Bottom, \
                    line.Prefix, line.PrefixGap, line.Suffix, line.SuffixGap, \
                    line.FieldCode, line.FieldPosition.Left, line.FieldPosition.Right, line.FieldPosition.Top, line.FieldPosition.Bottom, \
                    line.IsMarkupField])