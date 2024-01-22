### Statistics bot

ToDo:
- tests for all code
- add linter
- add logging
- get statistics for month, day, year

#### add local environment variable

`export CURRENCY_CACHE_TTL=3600`

#### run bot with auto restart

`nodemon --exec python3 main.py`

#### run autopep8

`autopep8 --exclude ./venv -ri .`

#### run tests

`todo`

#### build image (in directory with Dockerfile)

`docker build -t test .`

#### run container (in directory with .env file)

`docker run --rm --env-file .env test`
