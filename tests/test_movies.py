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


def test_index_page_is_served(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Content Review System" in response.data


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


def test_filter_by_multiple_languages_requires_all(client):
    _upload(client)
    # Only Jumanji lists both English and Français.
    response = client.get("/api/v1/movies?language=English&language=Français")
    titles = {item["title"] for item in response.get_json()["data"]["items"]}
    assert titles == {"Jumanji"}


def test_languages_endpoint_returns_distinct_sorted(client):
    _upload(client)
    languages = client.get("/api/v1/movies/languages").get_json()["data"]
    assert languages == ["English", "Français"]


def test_zero_vote_rating_sorts_last_like_null(client):
    rows = [
        "0,,en,Rated,a movie,2001-01-01,0,90,Released,Rated,6.0,100,1,18,['English']",
        "0,,en,Unrated,a movie,2002-01-01,0,90,Released,Unrated,9.0,0,1,18,['English']",
    ]
    body = "\n".join([CSV_HEADER, *rows])
    data = {"file": (io.BytesIO(body.encode("utf-8")), "movies.csv")}
    client.post("/api/v1/movies/upload", data=data, content_type="multipart/form-data")

    # Unrated has a higher average but zero votes, so it must sort last either way.
    for order in ("asc", "desc"):
        response = client.get(f"/api/v1/movies?sort_by=rating&sort_order={order}")
        titles = [item["title"] for item in response.get_json()["data"]["items"]]
        assert titles[-1] == "Unrated", f"zero-vote rating should sort last for {order}"


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


def test_records_without_release_date_sort_last(client):
    rows = [
        "0,,en,Has Date,a movie,2000-01-01,0,90,Released,Has Date,5.0,10,1,18,['English']",
        "0,,en,No Date,a movie,,0,90,Released,No Date,5.0,10,1,18,['English']",
    ]
    body = "\n".join([CSV_HEADER, *rows])
    data = {"file": (io.BytesIO(body.encode("utf-8")), "movies.csv")}
    client.post("/api/v1/movies/upload", data=data, content_type="multipart/form-data")

    for order in ("asc", "desc"):
        response = client.get(f"/api/v1/movies?sort_by=release_date&sort_order={order}")
        titles = [item["title"] for item in response.get_json()["data"]["items"]]
        assert titles[-1] == "No Date", f"null date should sort last for {order}"


def test_keyset_pagination_walks_every_record_once(client):
    _upload(client)  # 3 valid movies
    seen = []
    after = None
    for _ in range(10):  # generous guard against a runaway loop
        url = "/api/v1/movies?sort_by=rating&sort_order=desc&page_size=1"
        if after:
            url += f"&after={after}"
        data = client.get(url).get_json()["data"]
        seen.extend(item["title"] for item in data["items"])
        after = data["next_cursor"]
        if not after:
            break

    assert len(seen) == 3
    assert len(set(seen)) == 3  # no repeats, no gaps


def test_keyset_matches_offset_ordering(client):
    _upload(client)
    offset = [i["title"] for i in client.get("/api/v1/movies?sort_by=rating&sort_order=desc").get_json()["data"]["items"]]

    first = client.get("/api/v1/movies?sort_by=rating&sort_order=desc&page_size=2").get_json()["data"]
    nxt = client.get(f"/api/v1/movies?sort_by=rating&sort_order=desc&page_size=2&after={first['next_cursor']}").get_json()["data"]
    keyset = [i["title"] for i in first["items"]] + [i["title"] for i in nxt["items"]]

    assert keyset == offset


def test_bad_cursor_is_rejected(client):
    response = client.get("/api/v1/movies?sort_by=rating&after=not-a-real-cursor")
    assert response.status_code == 400
    assert response.get_json()["success"] is False


def test_internal_sort_flags_are_not_exposed(client):
    _upload(client)
    item = client.get("/api/v1/movies?page_size=1").get_json()["data"]["items"][0]
    assert "has_release_date" not in item
    assert "has_rating" not in item


def test_invalid_sort_by_is_rejected(client):
    response = client.get("/api/v1/movies?sort_by=budget")
    assert response.status_code == 400
    assert response.get_json()["success"] is False


def test_forbidden_role_is_blocked(client):
    response = client.get("/api/v1/movies", headers={"X-Role": "stranger"})
    assert response.status_code == 403
