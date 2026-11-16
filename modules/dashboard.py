
import streamlit as st
from modules.admin_ui import render_user_management
from modules.dataset_ui import render_dataset_management
from modules.cleaning_ui import render_data_cleaning
from modules.eda_ui import render_eda
from modules.insights_ui import render_insights
from modules.ai_assistant_ui import render_ai_assistant

def admin_dashboard(user):

    st.title("Admin Dashboard")

    st.write(f"Welcome, {user['name']}!")

    st.info("Administrator Control Panel")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Platform", "Active")

    with col2:
        st.metric("Role", "Administrator")

    with col3:
        st.metric("Access", "Full")

    st.divider()

    # Admin user management
    render_user_management()


def user_dashboard(user):

    st.title("User Dashboard")

    st.write(f"Welcome, {user['name']}!")

    st.info("Your Personal Workspace")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Account", "Active")

    with col2:
        st.metric("Role", "User")

    with col3:
        st.metric("Workspace", "Personal")

    st.divider()

    # Full-width dataset management section
    render_dataset_management(user)
    
    st.divider()
    render_data_cleaning(user)
    
    st.divider()
    render_eda(user)
    
    st.divider()
    render_insights(user)
    
    st.divider()
    render_ai_assistant(user)
    
