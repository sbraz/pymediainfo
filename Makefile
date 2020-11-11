all:
	tox -p

.PHONY: qa
qa:
	tox -p -e "black,flake8,isort,mypy,pylint"
