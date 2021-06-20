from pdf import pdfUtil
from pdf import pdf_parser
import os
from pathlib import Path
import pandas as pd

def test_markup_pdf(mocker):
    path = Path(os.getenv('PYTHONPATH'))
    data_file = os.path.join(path, "tests/data/test.csv")
    pdf_file = os.path.join(path, "tests/data/test.pdf")
    output_pdf = os.path.join(path, "tests/data/test-out.pdf")
    pdfUtil.markup_pdf(pd.read_csv(data_file), pdf_file, output_pdf)
    assert os.path.exists(output_pdf) 
    os.remove(output_pdf)

def test_markup_pdf_with_rotated_page(mocker):
    path = Path(os.getenv('PYTHONPATH'))
    data_file = os.path.join(path, "tests/data/t2125.csv")
    pdf_file = os.path.join(path, "tests/data/t2125.pdf")
    output_pdf = os.path.join(path, "tests/data/t2125-out.pdf")
    pdfUtil.markup_pdf(pd.read_csv(data_file), pdf_file, output_pdf)
    assert os.path.exists(output_pdf) 
    os.remove(output_pdf)

def test_save_pdf_pages(mocker):
    path = Path(os.getenv('PYTHONPATH'))
    pdf_file = os.path.join(path, "tests/data/test.pdf")
    csv_file = os.path.join(path, "tests/data/test-pages.csv")
    stats = [0, 0]
    pages = pdf_parser.parse_pdf(pdf_file, False, stats)
    pdfUtil.save_pdf_pages_tocsv("test.pdf", pages, csv_file)
    assert os.path.exists(csv_file) 
    os.remove(csv_file)