from datetime import date, timedelta
from collections import defaultdict
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import numpy as np

from gitlab_utils import users, projects, commits, merge_requests, issues
from modes.batch_mode import DEFAULT_ICFAI_USERS, DEFAULT_RCTS_USERS


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


def render_contribution_heatmap(start_date, end_date, daily_data, contribution_type="total"):
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


def render_contribution_mapping(client):
    """
    Renders the Contribution Mapping UI with calendar heatmap visualization.
    """
    st.title("Contribution Mapping")
    st.markdown("Visualize user contributions over time with a calendar heatmap view.")

    # Username Input - Now with Batch Selection
    st.subheader("1. Select User/Batch")

    # Step 1: Select Batch or Custom
    batch_choice = st.radio(
        "Choose option:",
        ["Batch 2026 ICFAI", "Batch 2026 RCTS", "Custom Username"],
        key="contrib_batch_choice"
    )

    username_input = ""

    if batch_choice == "Batch 2026 ICFAI":
        # Parse ICFAI users
        icfai_users = [u.strip() for u in DEFAULT_ICFAI_USERS.strip().split('\n') if u.strip()]
        selected_username = st.selectbox(
            "Select ICFAI User",
            icfai_users,
            key="contrib_icfai_user"
        )
        username_input = selected_username

    elif batch_choice == "Batch 2026 RCTS":
        # Parse RCTS users
        rcts_users = [u.strip() for u in DEFAULT_RCTS_USERS.strip().split('\n') if u.strip()]
        selected_username = st.selectbox(
            "Select RCTS User",
            rcts_users,
            key="contrib_rcts_user"
        )
        username_input = selected_username

    else:  # Custom Username
        username_input = st.text_input(
            "Enter GitLab Username",
            placeholder="e.g., johndoe",
            key="contrib_custom_username"
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
            st.session_state.contribution_generated = True

    # Fetch and Display Data
    if st.session_state.get("contribution_generated", False):
        username = st.session_state.get("map_username", "")
        filter_start = st.session_state.get("map_start_date")
        filter_end = st.session_state.get("map_end_date")

        with st.spinner(f"Fetching contribution data for '{username}'..."):
            # Get user info
            user_info = users.get_user_by_username(client, username)

            if not user_info:
                st.error(f"❌ User '{username}' not found.")
                st.session_state.contribution_generated = False
                return

            user_id = user_info.get("id")

            # Fetch all necessary data
            proj_data = projects.get_user_projects(client, user_id, username)
            all_projs = proj_data["all"]

            # Get commits
            all_commits, commit_counts, commit_stats = commits.get_user_commits(
                client, user_info, all_projs
            )

            # Get MRs
            user_mrs, mr_stats = merge_requests.get_user_mrs(client, user_id)

            # Get Issues
            user_issues, issue_stats = issues.get_user_issues(client, user_id)

        # Filter commits by date range
        filtered_commits = []
        for commit in all_commits:
            try:
                commit_date = pd.to_datetime(commit["date"]).date()
                if filter_start <= commit_date <= filter_end:
                    filtered_commits.append(commit)
            except:
                pass

        # Filter MRs by date range
        filtered_mrs = []
        mr_filtered_stats = {"total": 0, "merged": 0, "closed": 0, "opened": 0, "pending": 0}
        for mr in user_mrs:
            try:
                mr_date = pd.to_datetime(mr.get("created_at")).date()
                if filter_start <= mr_date <= filter_end:
                    filtered_mrs.append(mr)
                    mr_filtered_stats["total"] += 1
                    if mr.get("state") == "merged":
                        mr_filtered_stats["merged"] += 1
                    elif mr.get("state") == "closed":
                        mr_filtered_stats["closed"] += 1
                    elif mr.get("state") == "opened":
                        mr_filtered_stats["opened"] += 1
                        mr_filtered_stats["pending"] += 1
            except:
                pass

        # Filter Issues by date range
        filtered_issues = []
        issue_filtered_stats = {"total": 0, "opened": 0, "closed": 0}
        for issue in user_issues:
            try:
                issue_date = pd.to_datetime(issue.get("created_at")).date()
                if filter_start <= issue_date <= filter_end:
                    filtered_issues.append(issue)
                    issue_filtered_stats["total"] += 1
                    if issue.get("state") == "opened":
                        issue_filtered_stats["opened"] += 1
                    elif issue.get("state") == "closed":
                        issue_filtered_stats["closed"] += 1
            except:
                pass

        # Aggregate contributions by date for heatmap
        commits_by_date = {}
        for commit in filtered_commits:
            dk = commit["date"]
            commits_by_date[dk] = commits_by_date.get(dk, 0) + 1

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
            f"**📅 Viewing:** {filter_start.strftime('%Y-%m-%d')} to {filter_end.strftime('%Y-%m-%d')}"
        )

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

        # Detailed Date Range Breakdown
        st.subheader("📈 Date Range Breakdown")

        breakdown_cols = st.columns(3)
        with breakdown_cols[0]:
            st.write("**Commits by Status:**")
            st.markdown(f"- Total: **{total_commits}**")
            st.markdown(f"- Date Range: **{(filter_end - filter_start).days + 1} days**")
            st.markdown(
                f"- Avg per day: **{total_commits / max((filter_end - filter_start).days + 1, 1):.1f}**"
            )

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

        # Create daily summary
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
                    # Capture selection from heatmap
                    selection = st.plotly_chart(
                        fig,
                        use_container_width=False,
                        key=f"heatmap_{contrib_type}",
                        on_select="rerun",
                        selection_mode="points"
                    )

                    # Handle selection explicitly
                    points = selection.get("selection", {}).get("points", []) if selection else []
                    if not points:
                        # Fallback to session state key
                        state_sel = st.session_state.get(f"heatmap_{contrib_type}")
                        if state_sel and isinstance(state_sel, dict):
                            points = state_sel.get("selection", {}).get("points", [])

                    if points:
                        new_date = points[0].get("customdata")
                        if new_date:
                            st.session_state.selected_date = new_date
                else:
                    st.warning("No data to display.")
            else:
                st.warning("No contribution data available.")

        # Selected Day Details - GitLab style
        selected_date = st.session_state.get("selected_date")
        if selected_date:
            st.subheader(f"Contributions for {pd.to_datetime(selected_date).strftime('%b %d, %Y')}")

            with st.spinner("Fetching event details..."):
                day_start = selected_date
                day_end = (pd.to_datetime(selected_date) + timedelta(days=1)).strftime("%Y-%m-%d")

                day_events = users.get_user_events(client, user_id, after=day_start, before=day_end)

            if day_events:
                # Group and sort events (newest first)
                day_events = sorted(day_events, key=lambda x: x.get("created_at"), reverse=True)

                for event in day_events:
                    created_at = pd.to_datetime(event.get("created_at"))
                    # Convert to IST context (assuming UTC based on GitLab API)
                    created_at_ist = created_at + timedelta(hours=5, minutes=30)
                    time_str = created_at_ist.strftime("%I:%M%p").lower()

                    action = event.get("action_name")
                    target = event.get("target_type")
                    title = event.get("target_title") or event.get("push_data", {}).get("ref") or ""

                    # Project Info
                    proj_id = event.get("project_id")
                    # Try to find project name from existing data if possible, else just ID
                    p_name = f"Project {proj_id}"
                    for p in all_projs:
                        if p.get("id") == proj_id:
                            p_name = p.get("name_with_namespace")
                            break

                    # Formatting logic to match GitLab style
                    action_msg = action
                    if action == "pushed to":
                        ref = event.get("push_data", {}).get("ref")
                        count = event.get("push_data", {}).get("commit_count", 0)
                        action_msg = f"pushed to branch **{ref}** ({count} commits)"
                    elif action == "opened" and target == "MergeRequest":
                        action_msg = f"opened merge request **!{event.get('target_iid')}**"
                    elif action == "commented on":
                        action_msg = f"commented on {target.lower() if target else 'item'} **{event.get('target_iid') or ''}**"
                    elif action == "accepted" or action == "merged":
                        action_msg = f"merged merge request **!{event.get('target_iid')}**"

                    st.markdown(f"**{time_str}** — {action_msg} at **{p_name}**")
                    if title and action != "pushed to":
                        st.caption(f"&nbsp;&nbsp;&nbsp;&nbsp;{title}")

                st.markdown("")
            else:
                st.write("No detailed event history available for this day.")
