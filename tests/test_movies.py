import io

CSV_HEADER = (
    "budget,homepage,original_language,original_title,overview,release_date,"
    "revenue,runtime,status,title,vote_average,vote_count,"
    "production_company_id,genre_id,languages"
)

CSV_ROWS = [
    "30000000,,en,Toy Story,A toy story,1995-10-30,373554033,81,Released,Toy Story,7.7,5415,3,16,['English']",
    "65000000,,en,Jumanji,A board game,1995-12-15,262797249,104,Released,Jumanji,6.9,2413,559,12,\"['English', 'Français']\"",
    "0,,fr,Amelie,A Paris tale,2001-04-25,33000000,122,Released,Amelie,8.0,3000,1,35,\"['Français']\"",
    ",,,,no title row,1999-01-01,,,,,,,,,",
]


def _upload(client):
    body = "\n".join([CSV_HEADER, *CSV_ROWS])
    data = {"file": (io.BytesIO(body.encode("utf-8")), "movies.csv")}
    return client.post("/api/v1/movies/upload", data=data, content_type="multipart/form-data")


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_upload_skips_rows_without_title(client):
    response = _upload(client)
    assert response.status_code == 201
    body = response.get_json()["data"]
    assert body == {"inserted": 3, "skipped": 1}


def test_list_is_paginated(client):
    _upload(client)
    response = client.get("/api/v1/movies?page=1&page_size=2")
    body = response.get_json()["data"]
    assert response.status_code == 200
    assert body["total"] == 3
    assert body["total_pages"] == 2
    assert len(body["items"]) == 2


def test_filter_by_year(client):
    _upload(client)
    response = client.get("/api/v1/movies?year=1995")
    body = response.get_json()["data"]
    assert body["total"] == 2
    assert {item["title"] for item in body["items"]} == {"Toy Story", "Jumanji"}


def test_filter_by_language_matches_readable_name(client):
    _upload(client)
    response = client.get("/api/v1/movies?language=Français")
    titles = {item["title"] for item in response.get_json()["data"]["items"]}
    assert titles == {"Jumanji", "Amelie"}


def test_sort_by_rating_descending(client):
    _upload(client)
    response = client.get("/api/v1/movies?sort_by=rating&sort_order=desc")
    ratings = [item["vote_average"] for item in response.get_json()["data"]["items"]]
    assert ratings == sorted(ratings, reverse=True)


def test_sort_by_release_date_ascending(client):
    _upload(client)
    response = client.get("/api/v1/movies?sort_by=release_date&sort_order=asc")
    dates = [item["release_date"] for item in response.get_json()["data"]["items"]]
    assert dates == sorted(dates)


def test_invalid_sort_by_is_rejected(client):
    response = client.get("/api/v1/movies?sort_by=budget")
    assert response.status_code == 400
    assert response.get_json()["success"] is False


def test_forbidden_role_is_blocked(client):
    response = client.get("/api/v1/movies", headers={"X-Role": "stranger"})
    assert response.status_code == 403
