.PHONY: test docs

test:
	tox

docs:
	cd docs && make html
