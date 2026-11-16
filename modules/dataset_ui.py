
import streamlit as st

from modules.dataset_manager import (
    save_uploaded_dataset,
    get_my_datasets,
    load_my_dataset,
    delete_my_dataset
)


def render_dataset_management(user):

    user_id = user["id"]

    st.header("My Datasets")
    st.write("Upload and manage your business datasets.")

    # Dataset upload
    st.subheader("Upload Dataset")

    with st.form("dataset_upload_form"):

        uploaded_file = st.file_uploader(
            "Choose a CSV or Excel file",
            type=["csv", "xlsx", "xls"]
        )

        submitted = st.form_submit_button("Upload Dataset")

        if submitted:

            if uploaded_file is None:
                st.warning("Please select a file first.")

            else:
                success, message, dataset_id = save_uploaded_dataset(
                    user_id,
                    uploaded_file
                )

                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

    st.divider()

    # Display saved datasets
    st.subheader("My Uploaded Files")

    datasets = get_my_datasets(user_id)

    if not datasets:
        st.info("You haven't uploaded any datasets yet.")
        return

    st.metric("Total Datasets", len(datasets))

    dataset_options = {
        f"{item['original_filename']} (ID: {item['id']})": item["id"]
        for item in datasets
    }

    selected_label = st.selectbox(
        "Select a dataset to preview",
        options=list(dataset_options.keys())
    )

    selected_id = dataset_options[selected_label]

    selected_dataset = next(
        item for item in datasets
        if item["id"] == selected_id
    )

    col1, col2 = st.columns(2)

    col1.metric("Rows", selected_dataset["row_count"])
    col2.metric("Columns", selected_dataset["column_count"])

    try:
        dataframe = load_my_dataset(selected_id, user_id)

        st.subheader("Dataset Preview")
        st.dataframe(dataframe.head(100), use_container_width=True)

        csv_data = dataframe.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download Dataset as CSV",
            data=csv_data,
            file_name="insightai_dataset.csv",
            mime="text/csv"
        )

    except Exception as error:
        st.error(f"Unable to load dataset: {error}")

    st.divider()

    st.subheader("Delete Dataset")

    if st.button("Delete Selected Dataset", type="secondary"):

        deleted = delete_my_dataset(selected_id, user_id)

        if deleted:
            st.success("Dataset deleted successfully.")
            st.rerun()
        else:
            st.error("Unable to delete this dataset.")
