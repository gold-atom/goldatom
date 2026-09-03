.PHONY: test vectors simulate transfer economics compile wheel clean

test:
	python3 -m unittest discover -s tests -v

vectors:
	python3 scripts/generate_test_vectors.py

simulate:
	python3 -m goldatom simulate --output examples/genesis.goldatom.json

transfer:
	python3 -m goldatom simulate --with-transfer --output examples/transferred.goldatom.json

economics:
	python3 simulation/issuance_regimes.py

compile:
	python3 -m compileall -q goldatom scripts tests

wheel:
	python3 -m pip wheel --no-deps --no-build-isolation -w dist .

clean:
	rm -rf build dist .venv goldatom.egg-info
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
