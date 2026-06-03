from app.common.errors import ApiError

ALLOWED_SORT = {"release_date", "rating"}
ALLOWED_ORDER = {"asc", "desc"}


def parse_list_params(args, default_page_size, max_page_size):
    """Validate and normalise the query string for the movie list endpoint."""
    sort_by = args.get("sort_by")
    if sort_by is not None and sort_by not in ALLOWED_SORT:
        raise ApiError(f"sort_by must be one of {sorted(ALLOWED_SORT)}")

    sort_order = args.get("sort_order", "asc")
    if sort_order not in ALLOWED_ORDER:
        raise ApiError(f"sort_order must be one of {sorted(ALLOWED_ORDER)}")

    return {
        "page": _int_param(args, "page", 1, minimum=1),
        "page_size": _int_param(args, "page_size", default_page_size, minimum=1, maximum=max_page_size),
        "year": _optional_int(args, "year"),
        "language": _optional_str(args, "language"),
        "sort_by": sort_by,
        "sort_order": sort_order,
        "after": _optional_str(args, "after"),
    }


def _int_param(args, name, default, *, minimum=None, maximum=None):
    value = _optional_int(args, name)
    if value is None:
        return default
    if minimum is not None and value < minimum:
        raise ApiError(f"{name} must be >= {minimum}")
    if maximum is not None and value > maximum:
        return maximum
    return value


def _optional_int(args, name):
    raw = args.get(name)
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except ValueError:
        raise ApiError(f"{name} must be an integer")


def _optional_str(args, name):
    raw = args.get(name)
    return raw.strip() if raw and raw.strip() else None
