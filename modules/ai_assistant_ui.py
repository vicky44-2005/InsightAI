
import streamlit as st

from modules.dataset_manager import (
    get_my_datasets,
    load_my_dataset
)

from modules.question_engine import answer_question


def render_ai_assistant(user):

    st.header("Ask InsightAI")
    st.write(
        "Ask questions about your uploaded datasets "
        "and receive AI-powered answers."
    )

    # Get only the logged-in user's datasets
    datasets = get_my_datasets(user["id"])

    if not datasets:
        st.info("Please upload a dataset before using the AI Assistant.")
        return

    # Create a lookup for the user's datasets
    dataset_lookup = {
        int(dataset["id"]): dataset
        for dataset in datasets
    }

    dataset_ids = list(dataset_lookup.keys())

    selected_dataset_id = st.selectbox(
        "Select a dataset",
        options=dataset_ids,
        format_func=lambda dataset_id: (
            dataset_lookup[dataset_id]["original_filename"]
        ),
        key=f"ai_dataset_select_{user['id']}"
    )

    # Load the selected dataset with ownership verification
    try:
        dataframe = load_my_dataset(
            selected_dataset_id,
            user["id"]
        )
    except Exception as error:
        st.error(f"Unable to load dataset: {error}")
        return

    st.success(
        f"Dataset loaded: {len(dataframe)} rows "
        f"and {len(dataframe.columns)} columns."
    )

    st.divider()

    st.subheader("Chat with your data")

    # Keep separate chat history for each user and dataset
    history_key = (
        f"ai_chat_{user['id']}_{selected_dataset_id}"
    )

    if history_key not in st.session_state:
        st.session_state[history_key] = []

    # Display previous messages
    for message in st.session_state[history_key]:

        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Ask a new question
    question = st.chat_input(
        "Ask something about your dataset...",
        key=f"ai_question_{user['id']}_{selected_dataset_id}"
    )

    if question:

        # Display and save the user's question
        st.session_state[history_key].append({
            "role": "user",
            "content": question
        })

        with st.chat_message("user"):
            st.markdown(question)

        # Generate Gemini response
        with st.chat_message("assistant"):

            with st.spinner("InsightAI is analyzing your data..."):

                try:
                    answer = answer_question(
                    dataframe,
                    question
)

                    if not answer:
                        answer = "Gemini returned an empty response."

                    st.markdown(answer)

                    st.session_state[history_key].append({
                        "role": "assistant",
                        "content": answer
                    })

                except Exception as error:
                    st.error(
                        "Unable to generate an answer. "
                        "Please try again."
                    )
                    st.caption(f"Technical details: {error}")
