from datetime import date, timedelta

import streamlit as st


def render_contribution_mapping(client):
    """
    Renders the Contribution Mapping UI (UI skeleton only).
    """
    st.title("Contribution Mapping")
    st.markdown("Visualize user contributions over time with a heatmap view.")

    st.markdown("---")

    # Username Input
    st.subheader("1. Select User")
    username_input = st.text_input(
        "Enter GitLab Username", placeholder="e.g., johndoe", key="contrib_username"
    )

    if username_input and not username_input.strip():
        st.warning("Username cannot be empty or only spaces.")

    # Date Range Picker (Separate)
    st.subheader("2. Select Date Range")
    col1, col2 = st.columns(2)

    today = date.today()
    default_start = today - timedelta(days=30)

    with col1:
        start_date = st.date_input("From Date", default_start)

    with col2:
        end_date = st.date_input("To Date", today)

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
            st.session_state.contribution_generated = True
            with st.spinner("Fetching contribution data..."):
                pass  # Placeholder for API call

    st.markdown("---")

    # Placeholders
    if st.session_state.get("contribution_generated", False):
        # Total Contributions
        st.subheader("📊 Total Contributions")
        with st.container():
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Commits", "-")
            c2.metric("Total MRs", "-")
            c3.metric("Total Issues", "-")
            c4.metric("Total Contributions", "-")

        st.markdown("---")

        # Contribution Heatmap
        st.subheader("🔥 Contribution Heatmap")
        with st.container():
            st.info("Heatmap will appear here.")

        st.markdown("---")

        # Selected Day Details
        st.subheader("📅 Selected Day Details")
        with st.container():
            if st.session_state.get("selected_date", None) is None:
                st.markdown("Click a heatmap cell to view details.")
            else:
                st.markdown(f"**Selected Date:** {st.session_state.selected_date}")
