
import streamlit as st

from modules.dataset_manager import (
    get_my_datasets,
    load_my_dataset
)

from modules.insights_engine import generate_business_insights


def render_insights(user):

    st.header("AI Business Insights")

    st.write(
        "Discover important patterns and findings "
        "from your business datasets."
    )

    datasets = get_my_datasets(user["id"])

    if not datasets:
        st.info("Upload a dataset to generate business insights.")
        return

    dataset_options = {
        f"{item['original_filename']} (ID: {item['id']})": item["id"]
        for item in datasets
    }

    selected_label = st.selectbox(
        "Select dataset for insights",
        options=list(dataset_options.keys()),
        key="insights_dataset_select"
    )

    selected_id = dataset_options[selected_label]

    try:
        data = load_my_dataset(selected_id, user["id"])
    except Exception as error:
        st.error(f"Unable to load dataset: {error}")
        return

    if st.button("Generate Business Insights", type="primary"):

        with st.spinner("Analyzing your dataset..."):

            insights = generate_business_insights(data)

            st.session_state["business_insights"] = insights
            st.session_state["insights_dataset_id"] = selected_id

    if (
        st.session_state.get("insights_dataset_id") == selected_id
        and "business_insights" in st.session_state
    ):

        st.divider()
        st.subheader("Your Business Insights")

        for number, insight in enumerate(
            st.session_state["business_insights"],
            start=1
        ):

            st.success(f"{number}. {insight}")
