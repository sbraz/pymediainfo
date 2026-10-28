.PHONY: all
all:
	tox -p

.PHONY: qa
qa:
	tox -p -e "pre-commit,docs,mypy"
