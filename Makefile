ifndef ENV
	ENV=dev
endif

PROJECT_NAME=book-with-python

build: dotenv
	DOCKER_BUILDKIT=0 docker compose -f environment/$(ENV).yml build --no-cache

up: dotenv
	docker compose -f environment/$(ENV).yml up --force-recreate

upd: dotenv
	docker compose -f environment/$(ENV).yml up -d --force-recreate

down:
	docker compose -f environment/$(ENV).yml down

dotenv:
	cp src/config/config-$(ENV).cfg src/config/config.cfg

stopdockers:
	docker stop $(docker ps -a -q)
