
import streamlit as st

from modules.auth import (
    create_initial_admin,
    authenticate_user,
    register_user
)

from modules.database import admin_exists


def render_initial_admin_setup():

    if admin_exists():
        return True

    st.title("Welcome to InsightAI")
    st.subheader("Initial Administrator Setup")

    st.info("Create your first administrator account.")

    with st.form("admin_setup_form"):

        name = st.text_input("Administrator Name")
        email = st.text_input("Administrator Email")
        password = st.text_input("Create Password", type="password")
        confirm = st.text_input("Confirm Password", type="password")

        submitted = st.form_submit_button("Create Admin Account")

        if submitted:

            if not name.strip() or not email.strip():
                st.error("Enter your name and email.")

            elif password != confirm:
                st.error("Passwords do not match.")

            else:
                success, message = create_initial_admin(
                    name, email, password
                )

                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

    return False


def render_login_page():

    st.title("Welcome to InsightAI")
    st.write("AI-Powered Business Intelligence Platform")

    login_tab, register_tab = st.tabs(["Login", "Register"])

    with login_tab:

        with st.form("login_form"):

            email = st.text_input("Email")
            password = st.text_input("Password", type="password")

            submitted = st.form_submit_button("Login")

            if submitted:

                user = authenticate_user(email, password)

                if user:
                    st.session_state["user"] = dict(user)
                    st.rerun()
                else:
                    st.error("Invalid email or password.")

    with register_tab:

        with st.form("register_form"):

            name = st.text_input("Full Name")
            email = st.text_input("Email", key="register_email")

            password = st.text_input(
                "Password",
                type="password",
                key="register_password"
            )

            confirm = st.text_input(
                "Confirm Password",
                type="password",
                key="register_confirm"
            )

            submitted = st.form_submit_button("Create Account")

            if submitted:

                if password != confirm:
                    st.error("Passwords do not match.")

                else:
                    success, message = register_user(
                        name, email, password
                    )

                    if success:
                        st.success(message)
                    else:
                        st.error(message)


def logout():

    if st.sidebar.button("Logout"):
        st.session_state.pop("user", None)
        st.rerun()
