import argparse, csv
from pdf import pdf_parser
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--debug", help="dump debugging files", action="store_true")
parser.add_argument("-f", "--pdf_file", help="extract feature data from PDF_FILE")
parser.add_argument("-t", "--train", help="extract training data from pdf files in TRAIN folder")
args = parser.parse_args()

debug = args.debug
files = []
stats = [0, 0]
if args.pdf_file:
    pdf_file = Path(args.pdf_file)
    csvFile = pdf_file.parent.absolute().joinpath(pdf_file.stem + ".csv")
    files.append(args.pdf_file)
elif args.train:
    csvFile = Path(args.train).joinpath("training.csv")
    logFile = Path(args.train).joinpath("training_log.csv")
    log_file = open(logFile, mode='w',  newline='')
    log_writer = csv.writer(log_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    log_writer.writerow(["FileName", "Total", "Found", "Percentage"])
    for pdf_file in Path(args.train).glob('**/*.pdf'):
        files.append(str(pdf_file))

with open(csvFile, mode='w',  newline='') as csv_file:
    csv_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    csv_writer.writerow(["FileName", "PageNum", "LineLeft", "LineRight", "LineTop", "LineBottom", "LineWidth", \
        "TopElement", "LeftPadding", "RightPadding", "HasCentLine", "HasComboLine", "FieldWidth", "FieldHeight", \
        "Prefix", "PrefixGap", "Suffix", "SuffixGap", "FieldCode", "FieldLeft", "FieldRight", "FieldTop", "FieldBottom", "IsMarkupField"])
    for pdfFile in files:
        print(pdfFile)
        pages = pdf_parser.parse_pdf(pdfFile, debug, stats)
        percent = 0
        if stats[0] > 0:
            percent = stats[1] / stats[0]
        if args.train:
            log_writer.writerow([pdfFile, stats[0], stats[1], percent])
        for i, page in enumerate(pages):
            for line in [x for x in page if x.IsHorizontal]:
                csv_writer.writerow([pdfFile, i + 1, line.Position.Left, line.Position.Right, line.Position.Top, line.Position.Bottom, \
                    line.LineWidth, str(line.TopElement).replace("ElementType.",""), line.LeftPadding, line.RightPadding, line.HasCentLine, line.HasComboLine, \
                    line.FieldPosition.Right - line.FieldPosition.Left, line.FieldPosition.Top - line.FieldPosition.Bottom, \
                    line.Prefix, line.PrefixGap, line.Suffix, line.SuffixGap, \
                    line.FieldCode, line.FieldPosition.Left, line.FieldPosition.Right, line.FieldPosition.Top, line.FieldPosition.Bottom, \
                    line.IsMarkupField])