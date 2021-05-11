import sys, os
from pdfrw import PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.colors import black
from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams, LTLine, LTRect, LTTextContainer
from models.TextLine import TextLine
from pdfUtil import find_lines, get_position, get_acro_key

pdfFile = sys.argv[1]
outFile = os.path.splitext(pdfFile)[0] + "-out.pdf"
debugFile = os.path.splitext(pdfFile)[0] + "-debug.pdf"

reader = PdfReader(pdfFile)
canvas = canvas.Canvas(debugFile)
form = canvas.acroForm
canvas.setStrokeColor(black)
canvas.setLineWidth(0.1)

for page_layout in extract_pages(pdf_file = pdfFile, laparams = LAParams(line_margin=0)):
    pageNum = page_layout.pageid
    pageWidth = page_layout.bbox[2]
    pageHeight = page_layout.bbox[3]
    canvas.setPageSize((pageWidth, pageHeight))

    # extract texts and lines
    textLines = []
    lines = []
    for element in page_layout:
        if isinstance(element, LTTextContainer):
            textLines.append(TextLine(element.get_text(), get_position(element.bbox)))
        if isinstance(element, LTRect):
            lines.extend(find_lines(element))
        if isinstance(element, LTLine):
            lines.extend(find_lines(element))

    # dump debug file

    # pdf_page = reader.pages[pageNum - 1]  
    # if pdf_page.Annots:
    #     annotations = pdf_page.Annots
    #     for annotation in annotations:
    #         key = get_acro_key(annotation)
    #         if "_R_" in key or "_B_" in key or "_S_" in key:
    #             position = annotation.Rect
    #             left = float(position[0])
    #             right = float(position[2])
    #             top = float(position[3])
    #             bottom = float(position[1])
    #             form.textfield(name=key, x=left, y=bottom, width=right-left, height=top-bottom, borderWidth=0, tooltip=key, fontSize=7)

    # dump text lines
    for textLine in textLines:
        left = textLine.Position.Left
        right = textLine.Position.Right
        top = textLine.Position.Top
        bottom = textLine.Position.Bottom
        form.textfield(value=textLine.Text, x=left, y=bottom, width=right-left, height=top-bottom, borderWidth=0, fontSize=7)
    
    # dump lines
    for line in lines:
        canvas.setLineWidth(line.LineWidth)
        canvas.line(line.Position.Left, line.Position.Bottom, line.Position.Right, line.Position.Top)
    canvas.showPage()         
canvas.save()
