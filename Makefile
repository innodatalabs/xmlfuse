all: test build

test:
	. .venv/bin/activate; PYTHONPATH=. pytest

build:
	. .venv/bin/activate; python setup.py bdist_wheel

clean:
	rm -rf build dist

venv:
	rm -rf .venv
	python3.6 -m venv .venv
	. .venv/bin/activate; pip install pip -U; pip install -r requirements.txt pytest wheel twine
