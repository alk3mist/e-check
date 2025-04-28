# E-Check

This project uses [uv](https://docs.astral.sh/uv/) to manage dependencies, etc.

## Start the project directly

At first, install dependencies:

```bash
uv sync --no-project-install
```

You'll also need a running Postgres instance. Project was tested with the 17th version of the PostgreSQL.

Create and modify the `.env` file(add your Postgres settings, etc.):

```bash
cd e-check
cp example.env .env
vim .env
```

To start app, activate the virtual environment and execute the Uvicorn command:

```bash
source .venv/bin/activate
uvicorn --app-dir=src e_check.main:app
```

or execute the command with uv without the venv activation:

```bash
uv run uvicorn --app-dir=src e_check.main:app
```

## Start using the docker-compose

Ensure your `.env` configured correctly. Note `POSTGRES_DB=db` is required.
Docker compose will pick it and pass variables to services.

```bash
docker compose up
```

## Tests

To run tests, either active the virtual environment or use `uv run` from the project root directory:

```bash
source .venv/bin/activate
pytest
```

```bash
uv run pytest
```

Note: tests use the testcontainers package(for Postgres), that uses Docker under the hood, so you'll need Docker to be installed in order to run tests.

## Documentation page

After starting your application, you may find the API's interactive documentation on
http://localhost:8000/docs or on http://localhost:8080/docs if you're using docker-compose.

Alternatively, you could use the Redoc read only documentation
http://localhost:8000/redoc or on http://localhost:8080/redoc for docker-compose.
