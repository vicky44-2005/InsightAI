
import streamlit as st

from modules.dataset_manager import (
    get_my_datasets,
    load_my_dataset
)

from modules.data_engine import (
    get_dataset_summary,
    get_missing_value_report,
    get_data_quality_report,
    clean_dataset,
    dataset_to_csv_bytes
)


def render_data_cleaning(user):

    st.header("Data Cleaning")
    st.write("Identify and fix data-quality problems in your datasets.")

    user_id = user["id"]

    datasets = get_my_datasets(user_id)

    if not datasets:
        st.info("Upload a dataset first to start cleaning.")
        return

    dataset_options = {
        f"{item['original_filename']} (ID: {item['id']})": item["id"]
        for item in datasets
    }

    selected_label = st.selectbox(
        "Select dataset for cleaning",
        options=list(dataset_options.keys()),
        key="cleaning_dataset_select"
    )

    selected_id = dataset_options[selected_label]

    try:
        original_data = load_my_dataset(selected_id, user_id)
    except Exception as error:
        st.error(f"Unable to load dataset: {error}")
        return

    st.divider()

    # Original dataset summary
    st.subheader("1. Original Dataset")

    summary = get_dataset_summary(original_data)

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Rows", summary["rows"])
    col2.metric("Columns", summary["columns"])
    col3.metric("Missing Cells", summary["missing_cells"])
    col4.metric("Duplicate Rows", summary["duplicate_rows"])

    # Data quality reports
    with st.expander("View Missing Value Report"):
        st.dataframe(
            get_missing_value_report(original_data),
            use_container_width=True
        )

    with st.expander("View Data Quality Report"):
        st.dataframe(
            get_data_quality_report(original_data),
            use_container_width=True
        )

    st.divider()

    # Cleaning options
    st.subheader("2. Choose Cleaning Options")

    remove_duplicates = st.checkbox(
        "Remove duplicate rows",
        value=True
    )

    fill_numeric = st.checkbox(
        "Fill missing numeric values with column mean",
        value=True
    )

    fill_text = st.checkbox(
        "Fill missing text values with Unknown",
        value=True
    )

    standardize_names = st.checkbox(
        "Standardize column names",
        value=True
    )

    if st.button("Clean Dataset", type="primary"):

        try:
            cleaned_data = clean_dataset(
                original_data,
                remove_duplicates=remove_duplicates,
                fill_numeric_missing=fill_numeric,
                fill_text_missing=fill_text,
                standardize_column_names=standardize_names
            )

            st.session_state["cleaned_dataset"] = cleaned_data
            st.session_state["cleaned_dataset_id"] = selected_id

            st.success("Dataset cleaned successfully!")

        except Exception as error:
            st.error(f"Cleaning failed: {error}")

    # Display cleaning results
    if (
        "cleaned_dataset" in st.session_state
        and st.session_state.get("cleaned_dataset_id") == selected_id
    ):

        cleaned_data = st.session_state["cleaned_dataset"]

        st.divider()
        st.subheader("3. Cleaning Results")

        cleaned_summary = get_dataset_summary(cleaned_data)

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Original Rows",
            summary["rows"]
        )

        col2.metric(
            "Cleaned Rows",
            cleaned_summary["rows"],
            delta=cleaned_summary["rows"] - summary["rows"]
        )

        col3.metric(
            "Remaining Missing Cells",
            cleaned_summary["missing_cells"]
        )

        col4.metric(
            "Remaining Duplicates",
            cleaned_summary["duplicate_rows"]
        )

        st.subheader("Cleaned Dataset Preview")

        st.dataframe(
            cleaned_data.head(100),
            use_container_width=True
        )

        st.download_button(
            "Download Cleaned Dataset",
            data=dataset_to_csv_bytes(cleaned_data),
            file_name="insightai_cleaned_dataset.csv",
            mime="text/csv"
        )

        st.info(
            "Your original uploaded dataset remains unchanged. "
            "Download the cleaned copy to use it separately."
        )
