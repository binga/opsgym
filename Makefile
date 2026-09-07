.PHONY: test benchmark catalog site
test:
	PYTHONPATH=src python3 -m unittest discover -s tests -v
benchmark:
	PYTHONPATH=src python3 -m opsgym.cli --benchmark oracle --trials 1
catalog:
	PYTHONPATH=src python3 -m opsgym.cli --export-catalog website/data/catalog.json
site:
	python3 -m http.server 8080 --directory website
