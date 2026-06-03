# Content Upload and Review System

A Flask + MongoDB service for the content team to upload movie data from a CSV
file and browse it through a paginated, filterable and sortable API.

## Features

- **CSV upload** that streams rows into MongoDB in batches, so files up to 1GB
  are never loaded fully into memory.
- **Movie listing** with filtering by year of release and language, and sorting
  by release date or rating (ascending and descending). Sorts are index-backed
  and push empty values last; both offset and keyset (cursor) pagination are
  supported. See [Pagination, sorting and scale](#pagination-sorting-and-scale).
- Casbin-based authorization driven by a `model.conf` / `policy.csv` pair.

## Architecture

```mermaid
flowchart TD
    Client([Client]) -->|HTTP request| Auth{Casbin policy check}
    Auth -->|not allowed| Forbidden([403 Forbidden])
    Auth -->|allowed| Routes[Route layer<br/>/api/v1/movies]

    Routes --> Upload[POST /upload]
    Routes --> List[GET /]

    Upload --> ImportSvc[CSV import service<br/>stream rows, batch insert]
    List --> ListSvc[Movies service<br/>filter, sort, paginate]

    ImportSvc --> Mongo[(MongoDB)]
    ListSvc --> Mongo
```

A request first passes the casbin check in middleware, then a thin route hands
off to a service that does the work and talks to MongoDB. Indexes on `year`,
`original_language`, `languages`, `release_date` and `vote_average` back the
filters and sorts.

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

## Quick start with Docker

Brings up the API and MongoDB together with a single command:

```bash
docker compose up --build
```

The service is then available at `http://localhost:5000`. Stop it with
`docker compose down` (add `-v` to also drop the database volume).

## Manual setup

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

Then run the app:

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
| `after`      | Keyset cursor for deep pagination (see below)        |

**Sorting and empty values:** part of the source data has no `release_date`
(and some no `rating`). When sorting by such a field, those records are always
returned **last** — in both ascending and descending order. This is a
deliberate choice: the records are still included in the results and in
`total`, but real values are never pushed off the front of the list by empty
ones.

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
    "total_pages": 1,
    "next_cursor": "W3sidCI6ImJvb2wi...",
    "has_more": false
  }
}
```

## Pagination, sorting and scale

The CSV can be up to 1GB, so the list endpoint is built to stay fast as the
collection grows. The decisions below are deliberate.

**Sorting is index-backed, empty values last.** MongoDB has no native
`NULLS LAST`, and sorting on a value computed at query time forces a blocking
in-memory sort (capped at 100MB). Instead, a boolean flag (`has_release_date`,
`has_rating`) is computed once at upload time and indexed alongside the sort
field. The sort `{flag desc, field, _id}` is served entirely by an index
(`IXSCAN`, no `SORT` stage), and records with no value land last in both
directions while remaining in the results and the count.

**Two pagination modes, same sort.**

- *Offset* (default) — `page` / `page_size`, returns `total` and `total_pages`.
  Best for the CRM's page-number UI. `skip` cost grows with depth, so it is
  meant for shallow page jumps; `page_size` is capped at 100.
- *Keyset* (cursor) — pass `after=<next_cursor>` from the previous response to
  seek past the last seen record. Each page is an indexed lookup, so it stays
  fast at any depth. Use it for deep traversal or exporting the whole set.

```bash
# page 1
curl "http://localhost:5000/api/v1/movies?sort_by=rating&sort_order=desc&page_size=50"
# page 2 onward: feed back next_cursor
curl "http://localhost:5000/api/v1/movies?sort_by=rating&sort_order=desc&page_size=50&after=<next_cursor>"
```

Every response includes `next_cursor` and `has_more`, so a client can start on
offset and switch to keyset without changing the sort. Trade-off: keyset has no
"jump to page N" — that is what offset is for. The exact `total` count is only
computed in offset mode, since counting the full collection on every keyset page
would defeat the purpose.

## Testing

Integration tests run against an in-memory MongoDB (`mongomock`), so no database
is required:

```bash
pip install -r requirements-dev.txt
pytest
```

A Postman collection is available at
`postman/content-review-system.postman_collection.json`.
