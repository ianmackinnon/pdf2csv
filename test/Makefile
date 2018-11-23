SHELL := /bin/bash

all :
	./test_pdf2csv.py


eu : eu-20th-204 eu-20th-333 eu-20th-1020

OPTIONS := -vv

eu-20th-204 :
	../pdf2csv/pdf2csv.py $(OPTIONS) \
	  --border-width=1.5 \
	  --debug-dump-svg-path /tmp/$@.%04d.svg \
	  -o /tmp/$@.csv $@.pdf
	diff /tmp/$@.csv $@.csv
	diff /tmp/$@.0001.svg $@.0001.svg

eu-20th-333 :
	../pdf2csv/pdf2csv.py $(OPTIONS) \
	  --border-width=1.5 \
	  --debug-dump-svg-path /tmp/$@.%04d.svg \
	  -o /tmp/$@.csv $@.pdf
	diff /tmp/$@.csv $@.csv
	diff /tmp/$@.0001.svg $@.0001.svg

eu-20th-1020 :
	../pdf2csv/pdf2csv.py $(OPTIONS) \
	  --border-width=1.5 \
	  --debug-dump-svg-path /tmp/$@.%04d.svg \
	  -o /tmp/$@.csv $@.pdf
	diff /tmp/$@.csv $@.csv
	diff /tmp/$@.0001.svg $@.0001.svg
