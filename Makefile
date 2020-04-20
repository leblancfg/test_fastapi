.ONESHELL:

.PHONY: serve

serve:
	source env/bin/activate
	export GOOGLE_APPLICATION_CREDENTIALS="/home/leblancfg/gcred.json"
	uvicorn main:app --reload



