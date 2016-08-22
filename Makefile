.PHONY: test docs

help:
	@echo "  test       run tests (assumes you have python 2.7, 3.4, 3.5 installed)"
	@echo "  docs       builds documentation"
	@echo "  publish    push package as sdist and wheel to PyPI"


test:
	tox

docs:
	cd docs && make html

publish:
	 python setup.py sdist bdist_wheel upload
