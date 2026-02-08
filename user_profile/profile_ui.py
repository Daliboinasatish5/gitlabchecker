import streamlit as st

from user_profile.profile_utils import (
    process_commits,
    process_groups,
)


def render_user_profile(client, user_info):
    st.subheader(
        f"User: {user_info['name']} (@{user_info['username']}, ID: {user_info['id']})"
    )
    if user_info.get("avatar_url"):
        st.image(user_info["avatar_url"], width=80)
    st.markdown(f"[View GitLab Profile]({user_info.get('web_url', '')})")

    user_id = user_info["id"]

    try:
        groups = client.users.get_user_groups(user_id)
    except Exception:
        # Keep UI clean even if groups API is unavailable.
        groups = []

    # NOTE: Projects/Issues/MRs fetching intentionally left empty for now
    # (as requested; option should exist in UI, data handled by other team).
    projects = []

    try:
        commits_raw = client.users.get_user_commits(user_info)
    except Exception as e:
        st.warning(f"Could not load commits: {e}")
        commits_raw = []

    commit_rows = process_commits(commits_raw)
    group_rows = process_groups(groups)
    issue_rows = []
    mr_rows = []

    st.subheader("📊 Account Statistics")

    proj_count = len(projects)
    group_count = len(group_rows)
    issue_count = len(issue_rows)
    mr_count = len(mr_rows)

    cards = [
        ("Projects", proj_count),
        ("Groups", group_count),
        ("Issues", issue_count),
        ("Merge Requests", mr_count),
        ("Commits", len(commit_rows)),
    ]
    cols = st.columns(5)
    for idx, (label, value) in enumerate(cards):
        with cols[idx]:
            st.metric(label, value)

    st.markdown("---")
    st.subheader("📄 Detailed Report")

    st.markdown("#### Projects")
    st.info("Projects report is currently open and intentionally empty (handled by other team).")

    st.markdown("#### Groups")
    if not group_rows:
        st.info("No groups found.")
    else:
        st.dataframe(
            group_rows,
            width="stretch",
            column_config={
                "name": "Group name",
                "path": "Path",
                "visibility": "Visibility",
                "web_url": "Group URL",
            },
        )

    st.markdown("#### Issues")
    st.info("Issues report is currently open and intentionally empty (handled by other team).")

    st.markdown("#### Merge Requests")
    st.info("Merge Requests report is currently open and intentionally empty (handled by other team).")

    st.markdown("#### Commits")
    if not commit_rows:
        st.info("No commits found for this user.")
    else:
        st.dataframe(
            commit_rows,
            width="stretch",
            column_config={
                "project_type": "Project type",
                "project": "Project",
                "message": "Commit message",
                "date": "Date",
                "time": "Time",
                "slot": "Time slot",
            },
        )
