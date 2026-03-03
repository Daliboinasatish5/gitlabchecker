import os
from datetime import date, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from gitlab_utils import commits, issues, merge_requests, projects, users
from modes.batch_mode import DEFAULT_ICFAI_USERS, DEFAULT_RCTS_USERS


# Load team data
@st.cache_data
def load_team_data():
    """Load team and student data from CSV"""
    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "teams.csv")
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        return df
    return pd.DataFrame()


def calculate_streaks(commits_by_date, start_date, end_date):
    """Calculate longest streak and current streak"""
    if not commits_by_date:
        return 0, 0

    current_date = start_date
    current_streak = 0
    longest_streak = 0

    while current_date <= end_date:
        date_str = current_date.isoformat()
        if commits_by_date.get(date_str, 0) > 0:
            current_streak += 1
            longest_streak = max(longest_streak, current_streak)
        else:
            current_streak = 0
        current_date += timedelta(days=1)

    # Calculate current streak (from today backwards)
    current_streak = 0
    check_date = end_date
    while check_date >= start_date:
        date_str = check_date.isoformat()
        if commits_by_date.get(date_str, 0) > 0:
            current_streak += 1
        else:
            break
        check_date -= timedelta(days=1)

    return longest_streak, current_streak


@st.cache_data
def fetch_user_info_cached(_client, user_username):
    """Cache user info lookup"""
    return users.get_user_by_username(_client, user_username)


@st.cache_data
def fetch_user_projects_cached(_client, user_id, user_username):
    """Cache user projects lookup"""
    return projects.get_user_projects(_client, user_id, user_username)


@st.cache_data
def fetch_user_commits_cached(_client, user_info, all_projs):
    """Cache user commits lookup"""
    return commits.get_user_commits(_client, user_info, all_projs)


@st.cache_data
def fetch_user_mrs_cached(_client, user_id):
    """Cache user merge requests lookup"""
    return merge_requests.get_user_mrs(_client, user_id)


@st.cache_data
def fetch_user_issues_cached(_client, user_id):
    """Cache user issues lookup"""
    return issues.get_user_issues(_client, user_id)


def render_contribution_heatmap(start_date, end_date, daily_data, contribution_type="total"):  # noqa: C901
    """
    Render contribution heatmap with GitHub-style calendar layout.

    Args:
        start_date: Start date (date object)
        end_date: End date (date object)
        daily_data: List of dicts with keys: date, count, commits, mrs, issues
        contribution_type: 'total', 'commits', 'mrs', 'issues'

    Returns:
        plotly figure or None
    """
    if not start_date or not end_date:
        return None

    date_range = pd.date_range(start=start_date, end=end_date, freq="D")

    df_all = pd.DataFrame({"date": date_range})
    df_all["date"] = pd.to_datetime(df_all["date"])

    if daily_data:
        df_contrib = pd.DataFrame(daily_data)
        if not df_contrib.empty:
            df_contrib["date"] = pd.to_datetime(df_contrib["date"])

            if contribution_type == "total":
                df_contrib["count"] = df_contrib["count"]
            elif contribution_type == "commits":
                df_contrib["count"] = df_contrib["commits"]
            elif contribution_type == "mrs":
                df_contrib["count"] = df_contrib["mrs"]
            else:
                df_contrib["count"] = df_contrib["issues"]

            df_all = df_all.merge(df_contrib[["date", "count"]], on="date", how="left")

    max_count = max(1, df_all["count"].max())

    df_all["weekday"] = (df_all["date"].dt.weekday + 1) % 7
    df_all["week"] = df_all["date"].dt.isocalendar().week
    df_all["year"] = df_all["date"].dt.isocalendar().year
    df_all["month"] = df_all["date"].dt.strftime("%b")
    df_all["date_str"] = df_all["date"].dt.strftime("%Y-%m-%d")

    min_date = df_all["date"].min()
    first_week = int(df_all[df_all["date"] == min_date]["week"].values[0])
    df_all["week_offset"] = ((df_all["year"] - min_date.year) * 52) + (df_all["week"] - first_week)

    pivot = df_all.pivot(index="weekday", columns="week_offset", values="count")
    pivot = pivot.reindex(index=[0, 1, 2, 3, 4, 5, 6])

    pivot_dates = df_all.pivot(index="weekday", columns="week_offset", values="date_str")
    pivot_dates = pivot_dates.reindex(index=[0, 1, 2, 3, 4, 5, 6])

    day_labels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

    unique_months = df_all.drop_duplicates(subset=["date"]).copy()
    unique_months = unique_months.sort_values("date")

    month_ticks = []
    month_labels = []
    seen_months = set()
    for _, row in unique_months.iterrows():
        month = row["month"]
        week = int(row["week_offset"])
        if month not in seen_months:
            month_ticks.append(week)
            month_labels.append(month)
            seen_months.add(month)

    custom_colorscale = [
        [0, "#ebedf0"],
        [0.1, "#ccebff"],
        [0.4, "#66c2ff"],
        [0.7, "#0099ff"],
        [1, "#0055ff"],
    ]

    z_data = pivot.values.tolist()
    customdata = pivot_dates.values.tolist()

    for i in range(len(z_data)):
        for j in range(len(z_data[i])):
            if pd.isna(z_data[i][j]):
                z_data[i][j] = 0
            else:
                z_data[i][j] = int(z_data[i][j])

    for i in range(len(customdata)):
        for j in range(len(customdata[i])):
            if pd.isna(customdata[i][j]):
                customdata[i][j] = ""

    fig_width = len(pivot.columns) * 22 + 100

    fig = go.Figure(
        data=go.Heatmap(
            z=z_data,
            x=list(pivot.columns),
            y=day_labels,
            colorscale=custom_colorscale,
            zmin=0,
            zmax=max_count,
            showscale=False,
            customdata=customdata,
            hovertemplate="Date: %{customdata}<br>Contributions: %{z}<extra></extra>",
            xgap=2,
            ygap=2,
        )
    )

    fig.update_layout(
        xaxis={
            "showgrid": False,
            "zeroline": False,
            "showline": False,
            "showticklabels": True,
            "tickmode": "array",
            "tickvals": month_ticks,
            "ticktext": month_labels,
            "tickfont": {"size": 11, "color": "#57606a"},
            "range": [-0.5, len(pivot.columns) - 0.5],
            "side": "top",
        },
        yaxis={
            "showgrid": False,
            "zeroline": False,
            "showline": False,
            "showticklabels": True,
            "tickmode": "array",
            "tickvals": list(range(7)),
            "ticktext": day_labels,
            "tickfont": {"size": 10, "color": "#57606a"},
            "range": [6.5, -0.5],
            "scaleanchor": "x",
            "scaleratio": 1,
        },
        width=fig_width,
        height=280,
        margin={"l": 50, "r": 20, "t": 40, "b": 20},
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        hovermode="closest",
        clickmode="event+select",
        modebar_remove=[
            "zoom",
            "pan",
            "select",
            "lasso2d",
            "autoScale2d",
            "resetScale2d",
        ],
    )

    return fig


def render_contribution_mapping(client):  # noqa: C901
    """
    Renders the Contribution Mapping UI with calendar heatmap visualization.
    """
    st.title("Contribution Mapping")
    st.markdown("Visualize user contributions over time with a calendar heatmap view.")

    # Username Input - Now with Batch Selection
    st.subheader("1. Select User/Batch/Team")

    # Step 1: Select Batch, Team, or Custom
    batch_choice = st.radio(
        "Choose option:",
        ["Batch 2026 ICFAI", "Batch 2026 RCTS", "Team", "Custom Username"],
        key="contrib_batch_choice",
    )

    username_input = ""

    if batch_choice == "Batch 2026 ICFAI":
        # Parse ICFAI users
        icfai_users = [u.strip() for u in DEFAULT_ICFAI_USERS.strip().split("\n") if u.strip()]
        selected_username = st.selectbox("Select ICFAI User", icfai_users, key="contrib_icfai_user")
        username_input = selected_username

    elif batch_choice == "Batch 2026 RCTS":
        # Parse RCTS users
        rcts_users = [u.strip() for u in DEFAULT_RCTS_USERS.strip().split("\n") if u.strip()]
        selected_username = st.selectbox("Select RCTS User", rcts_users, key="contrib_rcts_user")
        username_input = selected_username

    elif batch_choice == "Team":
        # Load team data
        team_df = load_team_data()

        if not team_df.empty:
            # Get unique team names
            team_names = sorted(team_df["Team Name"].unique())

            selected_team = st.selectbox("Select Team", team_names, key="contrib_team_selector")

            # Get all students in selected team
            team_students = team_df[team_df["Team Name"] == selected_team]
            student_names = team_students["Student Name"].tolist()
            usernames = team_students["GitLab Username"].tolist()

            # Store team members info for later use
            if not team_students.empty:
                st.write(f"**Team:** {selected_team}")
                st.write(f"**Members:** {', '.join(student_names)}")
                # Store username list as comma-separated string for batch processing
                username_input = ",".join(usernames)
            else:
                st.warning("No students found in selected team")
        else:
            st.warning("Team data not available")

    else:  # Custom Username
        username_input = st.text_input(
            "Enter GitLab Username", placeholder="e.g., johndoe", key="contrib_custom_username"
        )

    if username_input and not username_input.strip():
        st.warning("Username cannot be empty or only spaces.")

    # Date Range Picker
    st.subheader("2. Select Date Range")
    col1, col2 = st.columns(2)

    today = date.today()
    default_start = today - timedelta(days=90)  # Last 3 months

    with col1:
        start_date = st.date_input("From Date", default_start)

    with col2:
        end_date = st.date_input("To Date", today)

    # Check if dates changed - if so, reset the generated flag
    if "selected_date" not in st.session_state:
        st.session_state.selected_date = None

    stored_user = st.session_state.get("map_username")
    if stored_user and username_input and username_input.strip() != stored_user:
        st.session_state.contribution_generated = False
        st.session_state.selected_date = None

    stored_start = st.session_state.get("map_start_date")
    stored_end = st.session_state.get("map_end_date")

    if stored_start and stored_end:
        if start_date != stored_start or end_date != stored_end:
            st.session_state.contribution_generated = False
            st.session_state.selected_date = None

    # Validation
    valid_range = True
    if start_date and end_date:
        if start_date > end_date:
            valid_range = False
            st.error("❌ From Date must be before To Date.")
    else:
        valid_range = False
        st.info("ℹ️ Please select both From Date and To Date.")

    # Generate Button
    st.subheader("3. Generate")
    generate_btn = st.button("Generate Contribution Map", key="contrib_generate")

    if generate_btn:
        if not username_input or not username_input.strip():
            st.error("❌ Please enter a valid username.")
        elif not valid_range:
            st.error("❌ Please select a valid date range.")
        else:
            st.session_state.map_username = username_input.strip()
            st.session_state.map_start_date = start_date
            st.session_state.map_end_date = end_date
            st.session_state.is_team_mode = batch_choice == "Team"
            st.session_state.contribution_generated = True

    # Fetch and Display Data
    if st.session_state.get("contribution_generated", False):
        username = st.session_state.get("map_username", "")
        filter_start = st.session_state.get("map_start_date")
        filter_end = st.session_state.get("map_end_date")
        is_team_mode = st.session_state.get("is_team_mode", False)

        # Handle multiple usernames for team mode
        usernames_list = (
            [u.strip() for u in username.split(",") if u.strip()] if is_team_mode else [username]
        )

        with st.spinner("Fetching contribution data..."):
            # Dictionary to store data for each user
            all_users_data = {}

            for user_username in usernames_list:
                # Get user info (cached)
                user_info = fetch_user_info_cached(client, user_username)

                if not user_info:
                    st.error(f"❌ User '{user_username}' not found.")
                    continue

                user_id = user_info.get("id")

                # Fetch all necessary data (cached)
                proj_data = fetch_user_projects_cached(client, user_id, user_username)
                all_projs = proj_data["all"]

                # Get commits (cached)
                all_commits, commit_counts, commit_stats = fetch_user_commits_cached(
                    client, user_info, all_projs
                )

                # Get MRs (cached)
                user_mrs, mr_stats = fetch_user_mrs_cached(client, user_id)

                # Get Issues (cached)
                user_issues, issue_stats = fetch_user_issues_cached(client, user_id)

                # Store in dictionary
                all_users_data[user_username] = {
                    "info": user_info,
                    "user_id": user_id,
                    "projects": all_projs,
                    "commits": all_commits,
                    "mrs": user_mrs,
                    "issues": user_issues,
                }

        # Filter commits by date range
        all_filtered_commits = []
        all_filtered_mrs = []
        all_filtered_issues = []

        for user_username, user_data in all_users_data.items():
            all_commits = user_data["commits"]
            user_mrs = user_data["mrs"]
            user_issues = user_data["issues"]

            # Filter commits by date range
            for commit in all_commits:
                try:
                    commit_date = pd.to_datetime(commit["date"]).date()
                    if filter_start <= commit_date <= filter_end:
                        commit["username"] = user_username  # Add username to commit
                        all_filtered_commits.append(commit)
                except Exception:
                    pass

            # Filter MRs by date range
            for mr in user_mrs:
                try:
                    mr_date = pd.to_datetime(mr.get("created_at")).date()
                    if filter_start <= mr_date <= filter_end:
                        mr["username"] = user_username  # Add username to MR
                        all_filtered_mrs.append(mr)
                except Exception:
                    pass

            # Filter Issues by date range
            for issue in user_issues:
                try:
                    issue_date = pd.to_datetime(issue.get("created_at")).date()
                    if filter_start <= issue_date <= filter_end:
                        issue["username"] = user_username  # Add username to issue
                        all_filtered_issues.append(issue)
                except Exception:
                    pass

        filtered_commits = all_filtered_commits
        filtered_mrs = all_filtered_mrs
        filtered_issues = all_filtered_issues

        # Aggregate contributions by date for heatmap
        commits_by_date = {}
        mr_filtered_stats = {"total": 0, "merged": 0, "closed": 0, "opened": 0, "pending": 0}
        issue_filtered_stats = {"total": 0, "opened": 0, "closed": 0}

        for commit in filtered_commits:
            dk = commit["date"]
            commits_by_date[dk] = commits_by_date.get(dk, 0) + 1

        for mr in filtered_mrs:
            mr_filtered_stats["total"] += 1
            if mr.get("state") == "merged":
                mr_filtered_stats["merged"] += 1
            elif mr.get("state") == "closed":
                mr_filtered_stats["closed"] += 1
            elif mr.get("state") == "opened":
                mr_filtered_stats["opened"] += 1
                mr_filtered_stats["pending"] += 1

        for issue in filtered_issues:
            issue_filtered_stats["total"] += 1
            if issue.get("state") == "opened":
                issue_filtered_stats["opened"] += 1
            elif issue.get("state") == "closed":
                issue_filtered_stats["closed"] += 1

        # --- Display Results ---

        # # User Info
        # col1, col2 = st.columns([1, 4])
        # with col1:
        #     if user_info.get("avatar_url"):
        #         st.image(user_info.get("avatar_url"), width=100)
        # with col2:
        #     st.markdown(f"### {user_info.get('name')} (@{user_info.get('username')})")
        #     st.markdown(f"**ID:** {user_id} | [GitLab Profile]({user_info.get('web_url')})")

        # st.markdown("---")

        # Calculate streaks
        longest_streak, current_streak = calculate_streaks(
            commits_by_date, filter_start, filter_end
        )
        total_commits = len(filtered_commits)

        # Summary Statistics
        st.subheader("📊 Contributions Summary")

        # Show date range being viewed
        st.markdown(
            f"**📅 Viewing:** {filter_start.strftime('%Y-%m-%d')} to "
            f"{filter_end.strftime('%Y-%m-%d')}"
        )

        # Show team members if in team mode
        if is_team_mode:
            team_members = [u.strip() for u in username.split(",") if u.strip()]
            st.markdown(f"**👥 Team Members:** {', '.join([f'@{u}' for u in team_members])}")

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Commits", total_commits)
        with col2:
            st.metric("Total MRs", mr_filtered_stats["total"])
        with col3:
            st.metric("Total Issues", issue_filtered_stats["total"])
        with col4:
            st.metric("Longest Streak", f"{longest_streak} days")
        with col5:
            st.metric("Current Streak", f"{current_streak} days")

        st.markdown("---")

        # Show per-member breakdown if in team mode
        if is_team_mode:
            st.subheader("👥 Per-Member Breakdown")
            team_members = [u.strip() for u in username.split(",") if u.strip()]

            member_cols = st.columns(len(team_members))
            for idx, member_username in enumerate(team_members):
                member_commits = [
                    c for c in filtered_commits if c.get("username") == member_username
                ]
                member_mrs = [mr for mr in filtered_mrs if mr.get("username") == member_username]
                member_issues = [
                    issue for issue in filtered_issues if issue.get("username") == member_username
                ]

                with member_cols[idx]:
                    st.markdown(f"**@{member_username}**")
                    st.metric("Commits", len(member_commits))
                    st.metric("MRs", len(member_mrs))
                    st.metric("Issues", len(member_issues))

            st.markdown("---")

        # Detailed Date Range Breakdown
        st.subheader("📈 Date Range Breakdown")

        breakdown_cols = st.columns(3)
        with breakdown_cols[0]:
            st.write("**Commits by Status:**")
            st.markdown(f"- Total: **{total_commits}**")
            st.markdown(f"- Date Range: **{(filter_end - filter_start).days + 1} days**")
            avg_per_day = total_commits / max((filter_end - filter_start).days + 1, 1)
            st.markdown(f"- Avg per day: **{avg_per_day:.1f}**")

        with breakdown_cols[1]:
            st.write("**MRs by Status:**")
            st.markdown(f"- Total: **{mr_filtered_stats['total']}**")
            st.markdown(f"- Merged: **{mr_filtered_stats['merged']}**")
            st.markdown(f"- Open: **{mr_filtered_stats['opened']}**")
            st.markdown(f"- Closed: **{mr_filtered_stats['closed']}**")

        with breakdown_cols[2]:
            st.write("**Issues by Status:**")
            st.markdown(f"- Total: **{issue_filtered_stats['total']}**")
            st.markdown(f"- Open: **{issue_filtered_stats['opened']}**")
            st.markdown(f"- Closed: **{issue_filtered_stats['closed']}**")

        st.markdown("---")

        # Daily Contribution Statistics
        st.subheader("📅 Daily Statistics")

        if is_team_mode:
            # Show detailed breakdown per team member
            team_members = [u.strip() for u in username.split(",") if u.strip()]
            st.markdown("**Breakdown by member:**")

            for member_username in team_members:
                with st.expander(f"@{member_username}"):
                    daily_summary = []
                    current_date = filter_start
                    while current_date <= filter_end:
                        date_str = current_date.isoformat()

                        # Count contributions for this member
                        member_commits = sum(
                            1
                            for c in filtered_commits
                            if c.get("username") == member_username and c.get("date") == date_str
                        )
                        member_mrs = sum(
                            1
                            for mr in filtered_mrs
                            if mr.get("username") == member_username
                            and pd.to_datetime(mr.get("created_at")).date() == current_date
                        )
                        member_issues = sum(
                            1
                            for issue in filtered_issues
                            if issue.get("username") == member_username
                            and pd.to_datetime(issue.get("created_at")).date() == current_date
                        )

                        if member_commits > 0 or member_mrs > 0 or member_issues > 0:
                            daily_summary.append(
                                {
                                    "Date": date_str,
                                    "Day": current_date.strftime("%A"),
                                    "Commits": member_commits,
                                    "MRs": member_mrs,
                                    "Issues": member_issues,
                                    "Total": member_commits + member_mrs + member_issues,
                                }
                            )

                        current_date += timedelta(days=1)

                    if daily_summary:
                        df_daily = pd.DataFrame(daily_summary)
                        st.dataframe(df_daily, use_container_width=True, hide_index=True)
                    else:
                        st.info(
                            f"No activity found for @{member_username} in the selected date range."
                        )
        else:
            # Original single-user daily summary
            daily_summary = []
            current_date = filter_start
            while current_date <= filter_end:
                date_str = current_date.isoformat()
                commit_count = commits_by_date.get(date_str, 0)

                # Count MRs on this date
                mr_count = sum(
                    1
                    for mr in filtered_mrs
                    if pd.to_datetime(mr.get("created_at")).date() == current_date
                )

                # Count Issues on this date
                issue_count = sum(
                    1
                    for issue in filtered_issues
                    if pd.to_datetime(issue.get("created_at")).date() == current_date
                )

                if commit_count > 0 or mr_count > 0 or issue_count > 0:
                    daily_summary.append(
                        {
                            "Date": date_str,
                            "Day": current_date.strftime("%A"),
                            "Commits": commit_count,
                            "MRs": mr_count,
                            "Issues": issue_count,
                            "Total": commit_count + mr_count + issue_count,
                        }
                    )

                current_date += timedelta(days=1)

            if daily_summary:
                df_daily = pd.DataFrame(daily_summary)
                st.dataframe(df_daily, use_container_width=True, hide_index=True)
            else:
                st.info("No activity found in the selected date range.")

        st.markdown("---")
        st.subheader("🔥 Contribution Activity")

        col_heatmap_title, col_heatmap_type = st.columns([3, 1])
        with col_heatmap_title:
            st.markdown("#### Contribution Heat Map")
        with col_heatmap_type:
            contrib_type = st.selectbox(
                "Type",
                ["total", "commits", "mrs", "issues"],
                format_func=lambda x: {
                    "total": "All",
                    "commits": "Commits",
                    "mrs": "MRs",
                    "issues": "Issues",
                }[x],
                key="contrib_type_heatmap",
                label_visibility="collapsed",
            )

        daily_data_for_heatmap = []
        current_date = filter_start
        while current_date <= filter_end:
            date_str = current_date.isoformat()
            commit_count = commits_by_date.get(date_str, 0)

            mr_count = sum(
                1
                for mr in filtered_mrs
                if pd.to_datetime(mr.get("created_at")).date() == current_date
            )

            issue_count = sum(
                1
                for issue in filtered_issues
                if pd.to_datetime(issue.get("created_at")).date() == current_date
            )

            daily_data_for_heatmap.append(
                {
                    "date": date_str,
                    "count": commit_count + mr_count + issue_count,
                    "commits": commit_count,
                    "mrs": mr_count,
                    "issues": issue_count,
                }
            )

            current_date += timedelta(days=1)

        with st.container():
            if daily_data_for_heatmap:
                fig = render_contribution_heatmap(
                    filter_start, filter_end, daily_data_for_heatmap, contrib_type
                )
                if fig:
                    # Add click event handling to Plotly figure
                    fig.update_layout(clickmode="event+select")
                    hover_template = (
                        "<b>Date: %{customdata}</b><br>Contributions: %{z}<br>"
                        "<i>Click to view details</i><extra></extra>"
                    )
                    fig.update_traces(
                        hovertemplate=hover_template,
                        customdata=fig.data[0].customdata if fig.data else None,
                    )

                    # Display the heatmap with click support
                    chart_key = f"heatmap_{contrib_type}"
                    st.plotly_chart(
                        fig,
                        use_container_width=False,
                        key=chart_key,
                        config={"responsive": True, "displayModeBar": False},
                    )

                    # Check if there's click data in session state and process it
                    if chart_key in st.session_state:
                        event_data = st.session_state[chart_key]
                        if event_data and isinstance(event_data, dict):
                            if "points" in event_data and event_data["points"]:
                                point = event_data["points"][0]
                                clicked_date = point.get("customdata")
                                if clicked_date:
                                    st.session_state.selected_date = clicked_date
                                    st.rerun()

                    # Manual date selector as reliable fallback
                    st.markdown("**📋 Or select a date manually:**")
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        manual_date = st.date_input(
                            "Select date to view contributions",
                            value=filter_end,
                            min_value=filter_start,
                            max_value=filter_end,
                            key=f"manual_date_{contrib_type}",
                            label_visibility="collapsed",
                        )
                    with col2:
                        if st.button(
                            "View", key=f"view_btn_{contrib_type}", use_container_width=True
                        ):
                            st.session_state.selected_date = manual_date.isoformat()
                else:
                    st.warning("No data to display.")
            else:
                st.warning("No contribution data available.")

        # Show contributions for selected date - displayed directly below heatmap
        selected_date = st.session_state.get("selected_date")
        if selected_date:
            st.markdown(
                f"**📅 Contributions for {pd.to_datetime(selected_date).strftime('%b %d, %Y')}**"
            )

            # Get commits for this date from filtered_commits
            day_commits = [c for c in filtered_commits if c.get("date") == selected_date]

            # Get MRs for this date
            day_mrs = [
                mr
                for mr in filtered_mrs
                if pd.to_datetime(mr.get("created_at")).date()
                == pd.to_datetime(selected_date).date()
            ]

            # Get Issues for this date
            day_issues = [
                issue
                for issue in filtered_issues
                if pd.to_datetime(issue.get("created_at")).date()
                == pd.to_datetime(selected_date).date()
            ]

            # Display summary with buttons to filter
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(
                    f"📝 Commits ({len(day_commits)})",
                    key="btn_commits",
                    use_container_width=True,
                ):
                    st.session_state.view_type = "commits"
            with col2:
                if st.button(
                    f"🔀 Merge Requests ({len(day_mrs)})",
                    key="btn_mrs",
                    use_container_width=True,
                ):
                    st.session_state.view_type = "mrs"
            with col3:
                if st.button(
                    f"❓ Issues ({len(day_issues)})",
                    key="btn_issues",
                    use_container_width=True,
                ):
                    st.session_state.view_type = "issues"

            st.markdown("---")

            # Get the selected view type (default to commits)
            view_type = st.session_state.get("view_type", "commits")

            # Display only the selected type
            if view_type == "commits":
                if day_commits:
                    st.markdown(f"### 📝 Commits ({len(day_commits)})")
                    for idx, commit in enumerate(day_commits, 1):
                        st.markdown(f"**{idx}. {commit.get('message', 'No message')}**")
                        st.caption(
                            f"🔗 {commit.get('project_name', 'Unknown Project')} | "
                            f"🔤 {commit.get('id', 'N/A')[:8]}"
                        )
                        st.markdown("")
                else:
                    st.info("No commits on this date")

            elif view_type == "mrs":
                if day_mrs:
                    st.markdown(f"### 🔀 Merge Requests ({len(day_mrs)})")
                    for idx, mr in enumerate(day_mrs, 1):
                        mr_iid = mr.get("iid", "N/A")
                        mr_title = mr.get("title", "No title")
                        mr_state = mr.get("state", "unknown").upper()
                        st.markdown(f"**{idx}. !{mr_iid} - {mr_title}**")
                        st.caption(f"Status: `{mr_state}`")
                        st.markdown("")
                else:
                    st.info("No merge requests on this date")

            elif view_type == "issues":
                if day_issues:
                    st.markdown(f"### ❓ Issues ({len(day_issues)})")
                    for idx, issue in enumerate(day_issues, 1):
                        issue_iid = issue.get("iid", "N/A")
                        issue_title = issue.get("title", "No title")
                        issue_state = issue.get("state", "unknown").upper()
                        st.markdown(f"**{idx}. #{issue_iid} - {issue_title}**")
                        st.caption(f"Status: `{issue_state}`")
                        st.markdown("")
                else:
                    st.info("No issues on this date")

            st.markdown("")
