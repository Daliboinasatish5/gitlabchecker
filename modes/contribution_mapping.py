from datetime import date, timedelta
from collections import defaultdict
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import numpy as np

from gitlab_utils import users, projects, commits, merge_requests, issues


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


def create_github_style_calendar(commits_by_date, start_date, end_date):
    """Create a GitHub-style contribution calendar with months across and days of week down"""

    # Create date range
    dates = []
    values = []
    current_date = start_date

    while current_date <= end_date:
        date_str = current_date.isoformat()
        count = commits_by_date.get(date_str, 0)
        dates.append(current_date)
        values.append(count)
        current_date += timedelta(days=1)

    # Create dataframe
    df = pd.DataFrame({
        'date': pd.to_datetime(dates),
        'commits': values,
    })

    # Adjust weekday so Sunday is first (GitHub style)
    df['weekday'] = (df['date'].dt.weekday + 1) % 7  # 0=Sunday, 1=Monday, ..., 6=Saturday
    df['year_month'] = df['date'].dt.to_period('M')
    df['week'] = df['date'].dt.isocalendar().week
    df['year'] = df['date'].dt.isocalendar().year
    df['year_week'] = df['year'].astype(str) + '-W' + df['week'].astype(str).str.zfill(2)

    # Get unique year-weeks to preserve chronological order
    unique_weeks = []
    for _, row in df.iterrows():
        year_week = row['year_week']
        if year_week not in unique_weeks:
            unique_weeks.append(year_week)

    # Create matrix for heatmap (7 rows for days, columns for weeks)
    z_data = [[] for _ in range(7)]
    hover_data = [[] for _ in range(7)]
    month_labels = []
    month_boundaries = []

    last_month = None
    col_idx = 0

    for year_week in unique_weeks:
        week_df = df[df['year_week'] == year_week]

        # Track month boundaries for annotation
        current_month = week_df.iloc[0]['year_month'] if len(week_df) > 0 else None
        if current_month != last_month and last_month is not None:
            month_boundaries.append(col_idx)
        if current_month != last_month:
            month_labels.append((col_idx, str(current_month)))
            last_month = current_month

        # For each day of week (0=Sunday to 6=Saturday)
        for day_idx in range(7):
            day_df = week_df[week_df['weekday'] == day_idx]

            if len(day_df) > 0:
                commits_val = int(day_df.iloc[0]['commits'])
                date_val = day_df.iloc[0]['date']
                hover_text = f"{date_val.strftime('%A, %B %d, %Y')}<br>Commits: {commits_val}"
            else:
                commits_val = 0
                hover_text = f"No contributions"

            z_data[day_idx].append(commits_val)
            hover_data[day_idx].append(hover_text)

        col_idx += 1

    # Day labels (Sunday to Saturday like GitHub)
    y_labels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    x_labels = ['' for _ in range(len(unique_weeks))]

    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=x_labels,
        y=y_labels,
        colorscale='Greens',
        showscale=True,
        hovertext=hover_data,
        hovertemplate='%{hovertext}<extra></extra>',
        colorbar=dict(title="Commits", thickness=15, len=0.6, y=0.5),
        xgap=2,
        ygap=1,
    ))

    # Add month annotations
    annotations = []
    for col_idx, month_str in month_labels:
        month_obj = pd.Period(month_str, freq='M')
        month_name = month_obj.strftime('%b')
        annotations.append(
            dict(
                x=col_idx,
                y=-1.2,
                text=month_name,
                showarrow=False,
                xanchor='left',
                yanchor='top',
                font=dict(size=11, color='black')
            )
        )

    fig.update_layout(
        title="<b>Contribution Activity</b>",
        xaxis_title="",
        yaxis_title="",
        height=300,
        width=1400,
        template='plotly_white',
        hovermode='closest',
        xaxis=dict(showticklabels=False, showgrid=False),
        yaxis=dict(autorange="reversed", showgrid=False),
        margin=dict(l=60, r=80, t=80, b=100),
        font=dict(size=10),
        annotations=annotations,
        plot_bgcolor='white',
    )

    return fig


def render_contribution_mapping(client):
    """
    Renders the Contribution Mapping UI with calendar heatmap visualization.
    """
    st.title("Contribution Mapping")
    st.markdown("Visualize user contributions over time with a calendar heatmap view.")

    st.markdown("---")

    # Username Input
    st.subheader("1. Select User")
    username_input = st.text_input(
        "Enter GitLab Username", placeholder="e.g., johndoe", key="contrib_username"
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
    stored_start = st.session_state.get("map_start_date")
    stored_end = st.session_state.get("map_end_date")

    if stored_start and stored_end:
        if start_date != stored_start or end_date != stored_end:
            st.session_state.contribution_generated = False

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

    st.markdown("---")

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
        mr_filtered_stats = {
            "total": 0,
            "merged": 0,
            "closed": 0,
            "opened": 0,
            "pending": 0
        }
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
        issue_filtered_stats = {
            "total": 0,
            "opened": 0,
            "closed": 0
        }
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

        # Aggregate commits by date
        commits_by_date = defaultdict(int)
        for commit in filtered_commits:
            commits_by_date[commit["date"]] += 1

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
        longest_streak, current_streak = calculate_streaks(commits_by_date, filter_start, filter_end)
        total_commits = len(filtered_commits)

        # Summary Statistics
        st.subheader("📊 Contributions Summary")

        # Show date range being viewed
        st.markdown(f"**📅 Viewing:** {filter_start.strftime('%Y-%m-%d')} to {filter_end.strftime('%Y-%m-%d')}")

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
            st.markdown(f"- Avg per day: **{total_commits / max((filter_end - filter_start).days + 1, 1):.1f}**")

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
            mr_count = sum(1 for mr in filtered_mrs if pd.to_datetime(mr.get("created_at")).date() == current_date)

            # Count Issues on this date
            issue_count = sum(1 for issue in filtered_issues if pd.to_datetime(issue.get("created_at")).date() == current_date)

            if commit_count > 0 or mr_count > 0 or issue_count > 0:
                daily_summary.append({
                    "Date": date_str,
                    "Day": current_date.strftime("%A"),
                    "Commits": commit_count,
                    "MRs": mr_count,
                    "Issues": issue_count,
                    "Total": commit_count + mr_count + issue_count
                })

            current_date += timedelta(days=1)

        if daily_summary:
            df_daily = pd.DataFrame(daily_summary)
            st.dataframe(
                df_daily,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No activity found in the selected date range.")

        st.markdown("---")
        st.subheader("🔥 Contribution Activity")

        # Calendar heatmap period selector
        col_heatmap_title, col_heatmap_selector = st.columns([3, 1])
        with col_heatmap_title:
            st.markdown("#### Submissions Heat Map")
        with col_heatmap_selector:
            heatmap_period = st.selectbox(
                "Select Period",
                ["Last 3 Months", "Last 6 Months"],
                key="heatmap_period_selector",
                label_visibility="collapsed"
            )

        # Calculate heatmap date range based on selection
        heatmap_end = filter_end
        if heatmap_period == "Last 3 Months":
            heatmap_start = heatmap_end - timedelta(days=90)
        else:  # Last 6 Months
            heatmap_start = heatmap_end - timedelta(days=180)

        # Filter commits for heatmap period
        heatmap_commits_by_date = {}
        for date_str, count in commits_by_date.items():
            date_obj = pd.to_datetime(date_str).date()
            if heatmap_start <= date_obj <= heatmap_end:
                heatmap_commits_by_date[date_str] = count

        with st.container():
            if heatmap_commits_by_date:
                # Create and display GitHub-style heatmap
                fig = create_github_style_calendar(heatmap_commits_by_date, heatmap_start, heatmap_end)
                st.plotly_chart(fig, use_container_width=True)

                # Show max day in heatmap period
                max_commits_day = max(heatmap_commits_by_date, key=heatmap_commits_by_date.get)
                max_commits_count = heatmap_commits_by_date[max_commits_day]
                st.info(f"📈 Most active day: **{max_commits_day}** with **{max_commits_count} commits**")
            else:
                st.warning("No commits found in the selected period.")


        st.markdown("---")
