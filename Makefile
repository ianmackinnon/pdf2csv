SHELL := /bin/bash

NAME := pdf2csv

all :

clean : clean-packages clean-tests clean-python-cache

test :
	python3 setup.py test

coverage :
	pytest tests --cov
	coverage html -d /tmp/$(NAME)-coverage-html

coverage-view :
	xdg-open /tmp/$(NAME)-coverage-html/index.html

tox :
	tox


build-packages :
	python3 setup.py sdist bdist_wheel

clean-packages :
	rm -rf .eggs build dist $(NAME).egg-info

clean-tests :
	rm -rf .pytest_cache .tox

clean-python-cache :
	find . -name __pycache__ -exec rm -rf {} +


install-global-editable :
	sudo -H python3 -m pip install -e .

uninstall-global :
	cd / && sudo -H python3 -m pip uninstall -y $(NAME)

installed-version-global :
	python3 -c "import $(NAME); print($(NAME).__version__)"

