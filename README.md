# Secure Cloud API

A small Todo REST API built with FastAPI and PostgreSQL, packaged with Docker Compose. This portfolio project starts with a reproducible local environment and will progressively add cloud deployment, automation, monitoring, and security testing.

**Current stage:** Local API and database implementation. AWS, Terraform, GitHub Actions, and k3s are planned work.

## What it does

- Creates todos with validated titles and stores them in PostgreSQL.
- Lists todos in ascending ID order.
- Provides separate application and database health endpoints.
- Persists database data in a Docker named volume.
- Provides interactive API documentation through FastAPI.

The application image uses Python 3.14, and the database uses PostgreSQL 18. Python dependencies are pinned in [requirements.txt](requirements.txt).

## Quick start

### Prerequisites

- Git to clone the repository.
- Docker Engine or Docker Desktop with Docker Compose available through `docker compose`.
- Port `8000` available on your machine.
- `curl` for the request examples below, or a browser for the interactive documentation.

Run these commands from the cloned repository's root directory:

1. Create your local configuration:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and replace the placeholder with a local database password:

   ```dotenv
   POSTGRES_PASSWORD=replace_with_local_password
   ```

   `.env` is excluded from Git and the Docker build context.

2. Build and start both services:

   ```bash
   docker compose up --build -d
   ```

3. Check the containers and database readiness:

   ```bash
   docker compose ps
   docker compose exec db pg_isready -U todo_user -d todo_db
   ```

   On the first run, PostgreSQL needs time to initialize. Repeat the readiness check until it reports that it is accepting connections. Compose currently has no health checks or startup dependencies, so running containers alone do not confirm database readiness.

4. Verify the API:

   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8000/db-health
   ```

   Expected responses, respectively:

   ```json
   {"status":"ok"}
   ```

   ```json
   {"database":"connected"}
   ```

Open [Swagger UI](http://localhost:8000/docs) to try the endpoints, or [ReDoc](http://localhost:8000/redoc) to read the API reference. The OpenAPI schema is available at [`/openapi.json`](http://localhost:8000/openapi.json).

## API reference

Base URL: `http://localhost:8000`

| Method | Endpoint | Purpose | Success status |
| --- | --- | --- | --- |
| `GET` | `/health` | Check that the application responds; does not query the database | `200` |
| `GET` | `/db-health` | Check database connectivity by executing `SELECT 1` | `200` |
| `GET` | `/todos` | List all todos ordered by ID | `200` |
| `POST` | `/todos` | Create a todo | `201` |

### Create a todo

```bash
curl -i -X POST http://localhost:8000/todos \
  -H 'Content-Type: application/json' \
  -d '{"title":"Verify the local Docker setup"}'
```

Example response body (the generated ID may differ):

```json
{"id":1,"title":"Verify the local Docker setup","completed":false}
```

`title` is required and must contain between 1 and 255 characters. Invalid request bodies return HTTP `422`. New todos default to `completed: false`; the create endpoint only accepts `title` as a defined input field.

### List todos

```bash
curl http://localhost:8000/todos
```

Example response:

```json
[
  {"id":1,"title":"Verify the local Docker setup","completed":false}
]
```

An empty database returns `[]`. Updating, completing, and deleting todos are not implemented yet.

## Configuration and storage

Compose reads `POSTGRES_PASSWORD` from the root `.env` file and supplies it to both services. It also configures the API's database connection:

| API variable | Compose value | Purpose |
| --- | --- | --- |
| `DB_HOST` | `db` | Database service name on the Compose network |
| `DB_PORT` | `5432` | Internal PostgreSQL port |
| `DB_NAME` | `todo_db` | Database name |
| `DB_USER` | `todo_user` | Database user |
| `DB_PASSWORD` | Value of `POSTGRES_PASSWORD` | Database password |

The API is published on `127.0.0.1:8000`. PostgreSQL has no published host port; the API connects to it over the Compose network.

The `todo-postgres-data` named volume stores PostgreSQL data at `/var/lib/postgresql` inside the database container. [db/init.sql](db/init.sql) creates the `todos` table when PostgreSQL initializes an empty data directory. It is an initialization script, not a migration system: editing it does not update an existing database.

Changing `POSTGRES_PASSWORD` in `.env` also does not change the password stored in an initialized database. Keep the values consistent, or reset the disposable local database as described below.

## Everyday commands

```bash
# Inspect service status
docker compose ps

# Follow application and database logs (Ctrl+C exits the log viewer)
docker compose logs -f api db

# Rebuild the API after changing its source or dependencies
docker compose up --build -d api

# Open a PostgreSQL shell
docker compose exec db psql -U todo_user -d todo_db

# Stop and remove containers and the network, keeping database data
docker compose down
```

To reset the local database, run the following commands. **This permanently deletes the Compose database volume and all stored todos.**

```bash
docker compose down --volumes
docker compose up --build -d
```

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| Docker cannot connect to its daemon | Start Docker Engine or Docker Desktop, then retry. |
| Port `8000` is already in use | Stop the conflicting process, or change the host port in `compose.yaml` and adjust the example URLs. |
| `/health` works but `/db-health` or `/todos` fails | Check `docker compose logs db api`, confirm PostgreSQL is ready, and verify the configured password matches the initialized database. |
| `todos` table is missing after changing `init.sql` | Initialization scripts only run against an empty data directory. Apply the schema manually or reset the disposable local database. |

## Repository layout

```text
.
├── app/
│   ├── main.py          # FastAPI application, request model, and routes
│   └── database.py      # PostgreSQL connection configuration
├── db/
│   └── init.sql         # Initial todos schema
├── .env.example        # Local configuration template
├── compose.yaml        # API, database, network, and persistent volume
├── Dockerfile          # Python application image
├── requirements.txt    # Pinned Python dependencies
├── notes.md            # Development journal; some progress notes are historical
└── README.md
```

## Current scope and roadmap

The current implementation is a local development foundation. It has no authentication, authorization, application TLS configuration, or automated test suite. Database queries use parameterized values for todo creation, and the API port is bound to the host's loopback interface.

Planned work includes:

- Verify setup from a fresh clone and add automated API tests.
- Add service readiness checks and database migrations.
- Provision AWS infrastructure with Terraform.
- Automate validation and deployment with GitHub Actions.
- Explore k3s deployment, monitoring, and security testing.
