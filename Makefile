.PHONY: all
all:
	tox -p

.PHONY: qa
qa:
	tox -p -e "docs,black,flake8,isort,mypy,pylint"
