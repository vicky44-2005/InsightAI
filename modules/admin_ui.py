
import streamlit as st

from modules.database import (
    get_all_users,
    update_user_status,
    get_user_statistics
)


def render_user_management():

    st.header("User Management")

    total, active, inactive = get_user_statistics()

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Users", total)
    col2.metric("Active Users", active)
    col3.metric("Inactive Users", inactive)

    st.divider()

    st.subheader("Registered Users")

    users = get_all_users()

    if not users:
        st.info("No registered users found.")
        return

    for user in users:

        with st.container(border=True):

            col1, col2 = st.columns([3, 1])

            with col1:
                st.write(f"**{user['name']}**")
                st.caption(user["email"])
                st.caption(f"Account ID: {user['id']}")

                if user["is_active"]:
                    st.success("Active")
                else:
                    st.warning("Inactive")

            with col2:

                if user["is_active"]:

                    if st.button(
                        "Deactivate",
                        key=f"deactivate_{user['id']}"
                    ):
                        update_user_status(user["id"], False)
                        st.rerun()

                else:

                    if st.button(
                        "Activate",
                        key=f"activate_{user['id']}"
                    ):
                        update_user_status(user["id"], True)
                        st.rerun()
