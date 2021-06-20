from pdf import pdf_parser
import os
from pathlib import Path

def test_parse_pdf_no_debug(mocker):
    path = Path(os.getenv('PYTHONPATH'))
    pdf_file = os.path.join(path, "tests/data/test.pdf")
    stats = [0, 0]
    pages = pdf_parser.parse_pdf(pdf_file, False, stats)
    assert pages != None

def test_parse_pdf_with_debug(mocker):
    path = Path(os.getenv('PYTHONPATH'))
    pdf_file = os.path.join(path, "tests/data/test.pdf")
    debug_file = os.path.join(path, "tests/data/test-debug.pdf")
    stats = [0, 0]
    pages = pdf_parser.parse_pdf(pdf_file, True, stats)
    assert pages != None
    assert os.path.exists(debug_file)
    os.remove(debug_file)
    
def test_parse_and_match_fields(mocker):
    path = Path(os.getenv('PYTHONPATH'))
    pdf_file = os.path.join(path, "tests/data/train.pdf")
    stats = [0, 0]
    pages = pdf_parser.parse_pdf(pdf_file, False, stats)
    assert pages != None

def test_parse_and_match_fields_with_debug(mocker):
    path = Path(os.getenv('PYTHONPATH'))
    pdf_file = os.path.join(path, "tests/data/train.pdf")
    debug_file = os.path.join(path, "tests/data/train-debug.pdf")
    stats = [0, 0]
    pages = pdf_parser.parse_pdf(pdf_file, True, stats)
    assert pages != None
    assert os.path.exists(debug_file)
    assert stats[0] == 14
    assert stats[1] == 14
    os.remove(debug_file)