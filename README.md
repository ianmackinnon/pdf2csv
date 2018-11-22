# pdf2csv

Extract tabular data from PDF files by detecting table border lines.


## Usage

Use `stdout` or specify a target filename:

    pdf2csv.pdf > out.csv
    pdf2csv -o out.csv in.pdf

Specify a page range:

    pdf2csv -p 273-280 -o out.csv in.pdf


