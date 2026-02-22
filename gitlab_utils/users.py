def get_user_by_username(client, username):
    """
    Fetches a user by username.
    Returns the user dict or None if not found.
    """
    users = client._get("/users", params={"username": username})
    if users and isinstance(users, list) and len(users) > 0:
        return users[0]  # Exact match usually returns one
    return None
def get_user_events(client, user_id, after=None, before=None):
    """
    Fetches events for a specific user.
    """
    params = {}
    if after:
        params["after"] = after
    if before:
        params["before"] = before

    return client._get_paginated(f"/users/{user_id}/events", params=params, per_page=100, max_pages=5)
