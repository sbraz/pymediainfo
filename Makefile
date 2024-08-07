.PHONY: all
all:
	tox -p

.PHONY: qa
qa:
	tox -p -m qa
