run:
	python -m asib.cli

test:
	python -m unittest discover -s tests -v

dashboard:
	python -c "from asib.dashboard import run; run(host='0.0.0.0', port=8080)"

scenario:
	python run_asib.py compound

docker:
	docker compose up --build
