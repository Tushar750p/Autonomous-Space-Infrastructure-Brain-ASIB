run:
	python -m asib.cli

test:
	python -m unittest discover -s tests -v

selftest:
	python -m asib.selftest 5

benchmark:
	python run_benchmark.py --ticks 20

experiments:
	python run_experiments.py --ticks 20

dashboard:
	python -c "from asib.dashboard import run; run()"

scenario:
	python run_asib.py compound

docker:
	docker compose up --build
