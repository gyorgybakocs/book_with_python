ifndef ENV
	ENV=dev
endif

PROJECT_NAME=book-with-python

build:
	DOCKER_BUILDKIT=0 docker compose -f environment/$(ENV).yml build --no-cache

up:
	docker compose -f environment/$(ENV).yml up --force-recreate

upd:
	docker compose -f environment/$(ENV).yml up -d --force-recreate

down:
	docker compose -f environment/$(ENV).yml down

stopdockers:
	docker stop $(docker ps -a -q)
