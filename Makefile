.PHONY: requirements update-deps install-dev pip-tools touch

PREREQS = pyproject.toml
TARGETS = requirements.txt dev-requirements.txt

requirements: pip-tools $(TARGETS)

update-deps: pip-tools touch $(TARGETS)

install-dev: pip-tools $(TARGETS)
	pip-sync dev-requirements.txt
	rm -rf .tox

pip-tools:
	pip install --upgrade pip-tools pip==23.1 setuptools

touch:
	touch $(PREREQS)

requirements.txt: pyproject.toml
	pip-compile --upgrade --build-isolation --resolver=backtracking --output-file=$@ $<
	touch $@

dev-requirements.txt: pyproject.toml
	pip-compile --upgrade --build-isolation --resolver=backtracking --extra=dev --output-file=$@ $<
	touch $@
