
import streamlit as st
import pandas as pd
import plotly.express as px

from modules.dataset_manager import (
    get_my_datasets,
    load_my_dataset
)


def render_eda(user):

    st.header("Exploratory Data Analysis")
    st.write("Explore your business data using interactive charts and statistics.")

    user_id = user["id"]
    datasets = get_my_datasets(user_id)

    if not datasets:
        st.info("Upload a dataset first to start analysis.")
        return

    dataset_options = {
        f"{item['original_filename']} (ID: {item['id']})": item["id"]
        for item in datasets
    }

    selected_label = st.selectbox(
        "Select dataset for analysis",
        options=list(dataset_options.keys()),
        key="eda_dataset_select"
    )

    selected_id = dataset_options[selected_label]

    try:
        data = load_my_dataset(selected_id, user_id)
    except Exception as error:
        st.error(f"Unable to load dataset: {error}")
        return

    st.divider()

    # Dataset overview
    st.subheader("1. Dataset Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Rows", len(data))
    col2.metric("Total Columns", len(data.columns))
    col3.metric("Numeric Columns", len(data.select_dtypes(include="number").columns))
    col4.metric("Missing Cells", int(data.isna().sum().sum()))

    # Numeric statistics
    st.divider()
    st.subheader("2. Statistical Summary")

    numeric_data = data.select_dtypes(include="number")

    if not numeric_data.empty:
        st.dataframe(
            numeric_data.describe().round(2),
            use_container_width=True
        )
    else:
        st.info("No numeric columns are available for statistical analysis.")

    # Chart generation
    st.divider()
    st.subheader("3. Interactive Data Visualization")

    all_columns = list(data.columns)

    chart_type = st.selectbox(
        "Choose chart type",
        ["Bar Chart", "Line Chart", "Pie Chart", "Scatter Plot"]
    )

    x_column = st.selectbox(
        "Select category / X-axis",
        all_columns,
        key="eda_x_column"
    )

    numeric_columns = list(numeric_data.columns)

    if chart_type == "Pie Chart":

        if not numeric_columns:
            st.warning("A pie chart requires at least one numeric column.")
        else:
            value_column = st.selectbox(
                "Select values",
                numeric_columns,
                key="eda_pie_value"
            )

            chart_data = data.groupby(
                x_column, dropna=False
            )[value_column].sum().reset_index()

            fig = px.pie(
                chart_data,
                names=x_column,
                values=value_column,
                title=f"{value_column} by {x_column}"
            )

            st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Scatter Plot":

        if len(numeric_columns) < 2:
            st.warning("A scatter plot requires at least two numeric columns.")
        else:
            y_column = st.selectbox(
                "Select Y-axis",
                [column for column in numeric_columns if column != x_column]
                if x_column in numeric_columns else numeric_columns,
                key="eda_scatter_y"
            )

            if x_column in numeric_columns:
                fig = px.scatter(
                    data,
                    x=x_column,
                    y=y_column,
                    title=f"{y_column} vs {x_column}"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("For a scatter plot, select a numeric X-axis column.")

    else:

        if not numeric_columns:
            st.warning("This chart requires a numeric column.")
        else:
            y_column = st.selectbox(
                "Select numeric values",
                numeric_columns,
                key="eda_y_column"
            )

            if chart_type == "Bar Chart":
                chart_data = data.groupby(
                    x_column, dropna=False
                )[y_column].sum().reset_index()

                fig = px.bar(
                    chart_data,
                    x=x_column,
                    y=y_column,
                    title=f"{y_column} by {x_column}"
                )

            else:
                chart_data = data.copy()

                fig = px.line(
                    chart_data,
                    x=x_column,
                    y=y_column,
                    title=f"{y_column} Trend"
                )

            st.plotly_chart(fig, use_container_width=True)

    # Correlation analysis
    st.divider()
    st.subheader("4. Correlation Analysis")

    if len(numeric_columns) >= 2:
        correlation = numeric_data.corr()

        fig = px.imshow(
            correlation,
            text_auto=".2f",
            color_continuous_scale="RdBu_r",
            title="Correlation Heatmap",
            aspect="auto"
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("At least two numeric columns are required for correlation analysis.")
