.PHONY: install test smoke

install:
	python -m pip install -e .

test:
	python -m unittest discover -s tests -v

smoke:
	governed contract validate --contract $(PWD)/examples/repo-contract.example.json
	governed route explain --contract $(PWD)/examples/repo-contract.example.json --task $(PWD)/examples/task.example.json
