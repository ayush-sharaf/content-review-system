# Content Upload and Review System

A Flask + MongoDB service for the content team to upload movie data from a CSV
file and browse it through a paginated, filterable and sortable API.

## Features

- **CSV upload** that streams rows into MongoDB in batches, so files up to 1GB
  are never loaded fully into memory.
- **Movie listing** with pagination, filtering by year of release and language,
  and sorting by release date or rating (ascending and descending).
- Casbin-based authorization driven by a `model.conf` / `policy.csv` pair.

## Project layout

```
app/
  casbin/      authorization model and policy
  common/      response envelope, errors, query-param parsing
  middleware/  request-time policy enforcement
  models/      movie document schema and (de)serialization
  route/       HTTP endpoints (thin handlers)
  service/     business logic (CSV import, list queries)
  config.py    environment-driven settings
  db.py        MongoDB connection and indexes
tests/         integration tests (run against an in-memory MongoDB)
postman/       Postman collection
```

Routes stay thin and delegate to the service layer, keeping handlers easy to
read and the business logic independently testable.

## Setup

Requirements: Python 3.11+ and a reachable MongoDB instance.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # adjust MONGO_URI if needed
```

If you do not have MongoDB locally, start one with Docker:

```bash
docker run -d -p 27017:27017 --name content-review-mongo mongo:7
```

## Run

```bash
flask --app wsgi run            # development
# or
gunicorn wsgi:app -b 0.0.0.0:5000   # production-style
```

The service listens on `http://localhost:5000`.

## API

All movie endpoints sit under `/api/v1/movies` and expect an `X-Role` header
(defaults to `default_role`, which the bundled policy allows).

### Upload a CSV

```
POST /api/v1/movies/upload
Content-Type: multipart/form-data
field: file=<movies.csv>
```

```bash
curl -X POST http://localhost:5000/api/v1/movies/upload \
  -F "file=@/path/to/movies.csv"
```

Response:

```json
{ "success": true, "data": { "inserted": 45000, "skipped": 12 } }
```

Rows without a title are skipped and reported in `skipped`.

### List movies

```
GET /api/v1/movies
```

| Query param  | Description                                          |
|--------------|------------------------------------------------------|
| `page`       | Page number, default `1`                             |
| `page_size`  | Items per page, default `20`, capped at `100`        |
| `year`       | Filter by year of release                            |
| `language`   | Filter by language code (`en`) or name (`English`)   |
| `sort_by`    | `release_date` or `rating`                           |
| `sort_order` | `asc` or `desc`, default `asc`                        |

```bash
curl "http://localhost:5000/api/v1/movies?year=1995&language=English&sort_by=rating&sort_order=desc"
```

Response:

```json
{
  "success": true,
  "data": {
    "items": [ { "title": "Toy Story", "vote_average": 7.7, "...": "..." } ],
    "page": 1,
    "page_size": 20,
    "total": 2,
    "total_pages": 1
  }
}
```

## Testing

Integration tests run against an in-memory MongoDB (`mongomock`), so no database
is required:

```bash
pip install -r requirements-dev.txt
pytest
```

A Postman collection is available at
`postman/content-review-system.postman_collection.json`.
