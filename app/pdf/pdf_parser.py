import os
from pdfrw import PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.colors import black, red, green, blue
from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams, LTLine, LTRect, LTTextContainer, LTFigure
from pdf.models.TextLine import TextLine
from pdf.pdfUtil import find_lines, get_position, get_acro_key, merge_lines, split_lines, extract_line_features, match_fields

def extract_elements(textLines, lines, element):
    if isinstance(element, LTFigure):
        for child in element:
            extract_elements(textLines, lines, child)
    if isinstance(element, LTTextContainer):
        textLines.append(TextLine(element.get_text(), get_position(element.bbox)))
    if isinstance(element, LTRect):
        lines.extend(find_lines(element))
    if isinstance(element, LTLine):
        lines.extend(find_lines(element))

def parse_pdf(pdfFile, debug, stats, current_task=None):
    stats[0] = 0
    stats[1] = 0
    reader = PdfReader(pdfFile)

    if debug:
        debugFile = os.path.splitext(pdfFile)[0] + "-debug.pdf"
        pdf_canvas = canvas.Canvas(debugFile)
        form = pdf_canvas.acroForm
        pdf_canvas.setStrokeColor(black)
        pdf_canvas.setLineWidth(0.1)
        colors = [ black, red, green, blue ]

    pages = []
    for page_layout in extract_pages(pdf_file = pdfFile, laparams = LAParams(line_margin=0, char_margin=0.5)):
        pageNum = page_layout.pageid
        pageWidth = page_layout.bbox[2]
        pageHeight = page_layout.bbox[3]

        if current_task != None:
            current_task.update_state(state='PROGRESS', meta="Extracting page " + str(pageNum) + " of " + str(len(reader.pages)))
        
        # extract texts and lines
        textLines = []
        lines = []
        for element in page_layout:
            extract_elements(textLines, lines, element)

        # process lines
        merge_lines(lines)
        split_lines(lines)
        extract_line_features(lines, textLines, pageHeight)

        # match fields
        if (pageNum > len(reader.pages)):
            return pages
        pdf_page = reader.pages[pageNum - 1]
        if pdf_page.Annots and len(pdf_page.Annots) > 0:
            match_fields(pdf_page, lines, stats)
        pages.append(lines)

        # dump debugging info
        if debug:
            pdf_canvas.setPageSize((pageWidth, pageHeight))
            
            # dump text lines
            for textLine in textLines:
                left = textLine.Position.Left
                right = textLine.Position.Right
                top = textLine.Position.Top
                bottom = textLine.Position.Bottom
                form.textfield(value=textLine.Text, x=left, y=bottom, width=right-left, height=top-bottom, borderWidth=0, fontSize=7)
            
            # dump lines
            ci = 0
            i = 1
            for line in lines:
                pdf_canvas.setStrokeColor(colors[ci])
                ci = (ci + 1) % len(colors)
                pdf_canvas.setLineWidth(line.LineWidth)
                pdf_canvas.rect(line.Position.Left, line.Position.Bottom, line.Position.Right - line.Position.Left, line.Position.Top - line.Position.Bottom)
                # dump fields
                if (line.IsHorizontal):
                    value = "line_" + str(i)
                    if line.IsMarkupField:
                        value = line.FieldCode
                    form.textfield(value=value, x=line.FieldPosition.Left, y=line.FieldPosition.Bottom, width=line.FieldPosition.Right - line.FieldPosition.Left, height=line.FieldPosition.Top - line.FieldPosition.Bottom, borderWidth=0, fontSize=7)
                    i += 1
            pdf_canvas.showPage()

    if debug:        
        pdf_canvas.save()

    return pages