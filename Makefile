SHELL := /bin/bash
.PHONY : test

NAME := pdf2csv

all :

clean : clean-packages clean-python-cache

test :
	python3 setup.py test


build-packages :
	python3 setup.py sdist bdist_wheel

clean-packages :
	rm -rf build dist $(NAME).egg-info


clean-python-cache :
	find . -name __pycache__ -exec rm -rf {} +


install-global-editable :
	sudo -H python3 -m pip install -e .

uninstall-global :
	cd / && sudo -H python3 -m pip uninstall -y $(NAME)

installed-version-global :
	python3 -c "import pdf2csv; print(pdf2csv.__version__)"
