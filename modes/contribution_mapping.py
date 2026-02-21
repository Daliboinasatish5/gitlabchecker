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


def create_contribution_calendar_heatmap(commits_by_date, start_date, end_date):
    """Create a GitHub-style contribution calendar using Plotly"""
    
    import calendar
    
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
    
    # Create dataframe with week and day info
    df = pd.DataFrame({
        'date': dates,
        'commits': values,
        'week': [d.isocalendar()[1] for d in dates],
        'day': [d.weekday() for d in dates],
        'day_name': [d.strftime('%a') for d in dates],
        'month': [d.strftime('%b') for d in dates],
    })
    
    # Create heatmap using go.Heatmap
    # Pivot data: rows = day of week, columns = week number
    pivot_data = df.pivot_table(
        values='commits',
        index='day',
        columns='week',
        fill_value=0,
        aggfunc='first'
    )
    
    # Day names
    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    
    # Create hover text - match the shape of pivot_data
    hover_text = []
    for day_idx in range(7):
        row_hover = []
        for week_num in pivot_data.columns:
            # Find corresponding date
            matching_dates = df[(df['day'] == day_idx) & (df['week'] == week_num)]
            if len(matching_dates) > 0:
                date_val = matching_dates.iloc[0]['date']
                commits_val = int(matching_dates.iloc[0]['commits'])
                hover_text_val = f"{date_val.strftime('%Y-%m-%d')}<br>Commits: {commits_val}"
            else:
                hover_text_val = ""
            row_hover.append(hover_text_val)
        hover_text.append(row_hover)
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot_data.values,
        x=pivot_data.columns,
        y=[day_names[i] for i in range(min(len(pivot_data.index), 7))],
        colorscale='Greens',
        showscale=True,
        hovertext=hover_text,
        hovertemplate='%{hovertext}<extra></extra>',
        colorbar=dict(title="Commits"),
    ))
    
    fig.update_layout(
        title="Contribution Calendar",
        xaxis_title="Week",
        yaxis_title="Day of Week",
        height=300,
        width=1200,
        template='plotly_white',
        hovermode='closest',
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
    default_start = today - timedelta(days=365)

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

        # User Info
        col1, col2 = st.columns([1, 4])
        with col1:
            if user_info.get("avatar_url"):
                st.image(user_info.get("avatar_url"), width=100)
        with col2:
            st.markdown(f"### {user_info.get('name')} (@{user_info.get('username')})")
            st.markdown(f"**ID:** {user_id} | [GitLab Profile]({user_info.get('web_url')})")

        st.markdown("---")

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
        st.subheader("🔥 Contribution Calendar")
        with st.container():
            if commits_by_date:
                # Create and display heatmap
                fig = create_contribution_calendar_heatmap(commits_by_date, filter_start, filter_end)
                st.plotly_chart(fig, use_container_width=True)

                # Show max day
                max_commits_day = max(commits_by_date, key=commits_by_date.get)
                max_commits_count = commits_by_date[max_commits_day]
                st.info(f"📈 Most active day: **{max_commits_day}** with **{max_commits_count} commits**")
            else:
                st.warning("No commits found in the selected date range.")

        st.markdown("---")

        # Daily Breakdown Table
        st.subheader("📋 Daily Contribution Breakdown")
        with st.container():
            if filtered_commits:
                # Create a table showing commits per day
                breakdown_data = []
                current_date = filter_start
                while current_date <= filter_end:
                    date_str = current_date.isoformat()
                    count = commits_by_date.get(date_str, 0)
                    if count > 0:  # Only show days with commits
                        breakdown_data.append({
                            "Date": date_str,
                            "Day": current_date.strftime("%A"),
                            "Commits": count,
                            "📊": "🟩" * min(count, 15)  # Visual bar
                        })
                    current_date += timedelta(days=1)

                if breakdown_data:
                    df_breakdown = pd.DataFrame(breakdown_data)
                    st.dataframe(
                        df_breakdown,
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("No days with commits in the selected range.")
            else:
                st.info("No commits found in the selected date range.")
