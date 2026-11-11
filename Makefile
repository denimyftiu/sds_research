DC = docker compose run --rm lab
.PHONY: build test a b c
build:
	docker compose build lab
test:
	$(DC) test
a:
	$(DC) scan topic_a/benchmark artifacts/a/scans
	$(DC) score topic_a/labels.json artifacts/a/scans artifacts/a/scores.json
b:
	$(DC) pilot topic_b/pilot artifacts/b
c:
	$(DC) pilot_gates artifacts/b artifacts/c/policies.json
