
import streamlit as st
import pandas as pd
from pathlib import Path
from modules.database import initialize_database
from modules.auth_ui import render_initial_admin_setup
from modules.auth_ui import render_login_page, logout
from modules.database import admin_exists
from modules.dashboard import admin_dashboard, user_dashboard
initialize_database()
if not render_initial_admin_setup():
    st.stop()
    
    if not admin_exists():
      if not render_initial_admin_setup():
        st.stop()

if "user" not in st.session_state:
    render_login_page()
    st.stop()

current_user = st.session_state["user"]
if current_user["role"] == "admin":

    admin_dashboard(current_user)

else:

    user_dashboard(current_user)

st.stop()
st.sidebar.write(f"Welcome, {current_user['name']}")
st.sidebar.write(f"Role: {current_user['role'].capitalize()}")

logout()
# =========================================================
# 1. PAGE CONFIGURATION
# Keep this as the first Streamlit command.
# =========================================================

st.set_page_config(
    page_title="InsightAI | Business Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# 2. THEMES
# =========================================================


THEMES = {
    
"Dark": {
    "background": "#000000",
    "panel": "#111111",
    "text": "#FFFFFF",
    "muted": "#B3B3B3",
    "accent": "#00D4AA",
    "border": "#333333"
},

    "Light": {
        "background": "#F4F7FB",
        "panel": "#FFFFFF",
        "text": "#172033",
        "muted": "#64748B",
        "accent": "#0D9488",
        "border": "#DCE4EE"
    }
}

if "theme_choice" not in st.session_state:
    st.session_state.theme_choice = "Dark"

if st.session_state.theme_choice not in THEMES:
    st.session_state.theme_choice = "Dark"

theme = THEMES[st.session_state.theme_choice]


st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {theme["background"]};
        color: {theme["text"]};
    }}

    [data-testid="stSidebar"] {{
        background-color: {theme["panel"]};
        border-right: 1px solid {theme["border"]};
    }}

    h1, h2, h3, h4, p, label, li {{
        color: {theme["text"]};
    }}

    [data-testid="stMetric"] {{
        background-color: {theme["panel"]};
        border: 1px solid {theme["border"]};
        padding: 18px;
        border-radius: 14px;
    }}

    [data-testid="stMetricLabel"] {{
        color: {theme["muted"]};
    }}

    [data-testid="stMetricValue"] {{
        color: {theme["accent"]};
    }}

    div.stButton > button {{
        background-color: {theme["accent"]};
        color: #071A16;
        border: none;
        border-radius: 8px;
        font-weight: 600;
    }}

    div.stButton > button:hover {{
        opacity: 0.85;
        border: 1px solid {theme["accent"]};
    }}

    div[data-testid="stAlert"] {{
        border-radius: 10px;
    }}

    hr {{
        border-color: {theme["border"]};
    }}

    .insight-card {{
        background-color: {theme["panel"]};
        border: 1px solid {theme["border"]};
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 12px;
    }}

    .muted-text {{
        color: {theme["muted"]};
    }}
        [data-testid="stHeader"] {{
        background: transparent;
    }}

    [data-testid="stToolbar"] {{
        background: transparent;
    }}
  
    </style>
    """,
    unsafe_allow_html=True
)

# =========================================================
# 3. HELPER FUNCTIONS
# =========================================================

def format_number(value):
    """Format a number for dashboard display."""
    try:
        value = float(value)
        if abs(value) >= 1_000_000:
            return f"{value / 1_000_000:.2f}M"
        if abs(value) >= 1_000:
            return f"{value / 1_000:.2f}K"
        return f"{value:,.2f}"
    except (ValueError, TypeError):
        return str(value)


def get_numeric_columns(data):
    """Return numeric columns from a dataset."""
    return data.select_dtypes(include="number").columns.tolist()


def make_insights(data):
    """Generate simple insights from uploaded data."""
    insights = []
    numeric_cols = get_numeric_columns(data)

    if data.empty:
        return ["The uploaded dataset contains no rows."]

    insights.append(
        f"Your dataset contains {len(data):,} rows "
        f"and {len(data.columns)} columns."
    )

    missing_count = int(data.isna().sum().sum())
    if missing_count:
        insights.append(
            f"There are {missing_count:,} missing values "
            "that may need cleaning."
        )
    else:
        insights.append("No missing values were found.")

    duplicate_count = int(data.duplicated().sum())
    insights.append(
        f"The dataset contains {duplicate_count:,} duplicate rows."
    )

    if numeric_cols:
        col = numeric_cols[0]
        insights.append(
            f"The average value of '{col}' is "
            f"{format_number(data[col].mean())}."
        )

        highest = data[col].max()
        lowest = data[col].min()

        insights.append(
            f"The highest '{col}' value is "
            f"{format_number(highest)}, and the lowest is "
            f"{format_number(lowest)}."
        )

    return insights


def answer_question(data, question):
    """Answer common questions using the uploaded dataset."""
    q = question.lower().strip()
    numeric_cols = get_numeric_columns(data)

    if not q:
        return "Please enter a question."

    if data.empty:
        return "Your dataset is empty. Please upload a dataset with rows."

    if any(word in q for word in ["missing", "null", "empty values"]):
        missing = data.isna().sum()
        missing = missing[missing > 0]

        if missing.empty:
            return "There are no missing values in your dataset."

        return "Missing values by column:\n" + "\n".join(
            f"- {col}: {int(count)}"
            for col, count in missing.items()
        )

    if "duplicate" in q:
        return (
            f"Your dataset contains "
            f"{int(data.duplicated().sum())} duplicate rows."
        )

    if any(word in q for word in ["how many rows", "number of rows", "row count"]):
        return f"Your dataset has {len(data):,} rows."

    if any(word in q for word in ["how many columns", "number of columns", "column count"]):
        return (
            f"Your dataset has {len(data.columns)} columns: "
            + ", ".join(map(str, data.columns))
        )

    if any(word in q for word in ["average", "mean"]):
        for col in numeric_cols:
            if col.lower() in q:
                return (
                    f"The average of '{col}' is "
                    f"{format_number(data[col].mean())}."
                )

        if numeric_cols:
            col = numeric_cols[0]
            return (
                f"You didn't specify a numeric column, so here's the "
                f"average of '{col}': {format_number(data[col].mean())}."
            )

        return "There are no numeric columns to calculate an average."

    if any(word in q for word in ["total", "sum", "overall amount"]):
        for col in numeric_cols:
            if col.lower() in q:
                return (
                    f"The total of '{col}' is "
                    f"{format_number(data[col].sum())}."
                )

        if numeric_cols:
            col = numeric_cols[0]
            return (
                f"You didn't specify a numeric column, so here's the "
                f"total of '{col}': {format_number(data[col].sum())}."
            )

        return "There are no numeric columns to calculate a total."

    if any(word in q for word in ["highest", "maximum", "max", "largest"]):
        for col in numeric_cols:
            if col.lower() in q:
                return (
                    f"The highest value in '{col}' is "
                    f"{format_number(data[col].max())}."
                )

        if numeric_cols:
            col = numeric_cols[0]
            return (
                f"The highest value in '{col}' is "
                f"{format_number(data[col].max())}."
            )

    if any(word in q for word in ["lowest", "minimum", "min", "smallest"]):
        for col in numeric_cols:
            if col.lower() in q:
                return (
                    f"The lowest value in '{col}' is "
                    f"{format_number(data[col].min())}."
                )

        if numeric_cols:
            col = numeric_cols[0]
            return (
                f"The lowest value in '{col}' is "
                f"{format_number(data[col].min())}."
            )

    if "column" in q and any(word in q for word in ["list", "name", "show"]):
        return "Dataset columns:\n" + "\n".join(
            f"- {col}" for col in data.columns
        )

    return (
        "I can answer basic questions about totals, averages, highest "
        "and lowest values, missing values, duplicates, rows, and columns. "
        "Try asking: 'What is the total of Sales?' or "
        "'Are there any missing values?'"
    )


def make_forecast(series, periods=3):
    """Create a simple linear-trend forecast for a numeric series."""
    values = pd.to_numeric(series, errors="coerce").dropna().reset_index(drop=True)

    if len(values) < 2:
        return None

    # Use a straight-line trend based on the available observations.
    x_values = list(range(len(values)))
    slope, intercept = __import__("numpy").polyfit(x_values, values.tolist(), 1)

    forecast_x = list(range(len(values), len(values) + periods))
    forecast_values = [float(slope * x + intercept) for x in forecast_x]

    return pd.DataFrame({
        "Period": [f"Forecast {i + 1}" for i in range(periods)],
        "Predicted value": forecast_values
    })


# =========================================================
# 4. SIDEBAR NAVIGATION
# =========================================================

with st.sidebar:
    st.markdown("# 📊 InsightAI")
    st.caption("AI-powered business intelligence")

    st.divider()

    st.markdown("### 🎨 Dashboard Theme")

    st.selectbox(
        "Choose your theme",
        options=list(THEMES.keys()),
        key="theme_choice"
    )

    st.divider()

    page = st.radio(
        "Navigation",
        [
            "🏠 Dashboard",
            "📂 Data Upload",
            "📊 Analytics",
            "🤖 AI Assistant",
            "🔮 Forecast",
            "🧹 Data Quality"
        ]
    )

    st.divider()
    st.caption("Upload business data to begin analysis.")

# =========================================================
# 5. APPLICATION HEADER
# =========================================================

st.title("📊 InsightAI")
st.markdown(
    '<p class="muted-text">Turn your business data into useful insights.</p>',
    unsafe_allow_html=True
)


# =========================================================
# 6. DATA UPLOAD
# =========================================================

st.subheader("📂 Upload Your Business Dataset")

uploaded_file = st.file_uploader(
    "Choose a CSV or Excel file",
    type=["csv", "xlsx", "xls"],
    help="Upload your business data to start analyzing it."
)

if uploaded_file is not None:
    try:
        if uploaded_file.name.lower().endswith(".csv"):
            data = pd.read_csv(uploaded_file)
        else:
            data = pd.read_excel(uploaded_file)

        st.session_state["insightai_data"] = data
        st.session_state["insightai_filename"] = uploaded_file.name

    except Exception as error:
        st.error(f"Could not read this file: {error}")
        st.stop()

data = st.session_state.get("insightai_data")

if data is None:
    st.info("Upload a CSV or Excel file above to get started.")

    st.markdown("### What you can do with InsightAI")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 📈 Analytics")
        st.write("Explore numeric columns and create charts.")

    with col2:
        st.markdown("### 🤖 Data Assistant")
        st.write("Ask questions about your uploaded data.")

    with col3:
        st.markdown("### 🔮 Forecast")
        st.write("Estimate future values using a simple trend.")

    st.stop()

if data.empty:
    st.warning("The uploaded file has no data rows.")
    st.stop()

numeric_columns = get_numeric_columns(data)
all_columns = data.columns.tolist()

st.success(
    f"Loaded: {st.session_state.get('insightai_filename', 'Dataset')} "
    f"— {len(data):,} rows and {len(all_columns)} columns."
)


# =========================================================
# 7. DASHBOARD PAGE
# =========================================================

if page == "🏠 Dashboard":
    st.subheader("Business Overview")

    total_rows = len(data)
    total_columns = len(all_columns)
    missing_values = int(data.isna().sum().sum())
    duplicate_rows = int(data.duplicated().sum())

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total Rows", f"{total_rows:,}")
    c2.metric("Total Columns", f"{total_columns:,}")
    c3.metric("Missing Values", f"{missing_values:,}")
    c4.metric("Duplicate Rows", f"{duplicate_rows:,}")

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("Dataset Preview")
        st.dataframe(data.head(10), use_container_width=True)

    with right:
        st.subheader("Column Types")
        type_data = pd.DataFrame({
            "Column": data.columns.astype(str),
            "Data Type": [str(dtype) for dtype in data.dtypes]
        })
        st.dataframe(type_data, use_container_width=True, hide_index=True)

    st.subheader("Quick Insights")
    for insight in make_insights(data):
        st.markdown(f"- {insight}")

    if numeric_columns:
        st.subheader("Numeric Data Overview")
        selected_column = st.selectbox(
            "Choose a numeric column",
            numeric_columns,
            key="dashboard_numeric_column"
        )

        chart_data = data[[selected_column]].dropna().reset_index(drop=True)
        if not chart_data.empty:
            st.line_chart(chart_data, use_container_width=True)

# =========================================================
# 8. DATA UPLOAD PAGE
# =========================================================

elif page == "📂 Data Upload":
    st.subheader("Dataset Explorer")

    st.write("View your dataset and select which rows to display.")

    row_limit = st.slider(
        "Rows to display",
        min_value=5,
        max_value=max(5, min(100, len(data))),
        value=min(10, max(5, len(data)))
    )

    st.dataframe(
        data.head(row_limit),
        use_container_width=True,
        hide_index=True
    )

    st.subheader("Dataset Information")

    info_col1, info_col2 = st.columns(2)

    with info_col1:
        st.write("**Column names**")
        for column in all_columns:
            st.write(f"- {column}")

    with info_col2:
        st.write("**Data types**")
        for column, dtype in data.dtypes.items():
            st.write(f"- {column}: {dtype}")

    st.download_button(
        "⬇️ Download Current Dataset as CSV",
        data=data.to_csv(index=False).encode("utf-8"),
        file_name="insightai_dataset.csv",
        mime="text/csv"
    )

# =========================================================
# 9. ANALYTICS PAGE
# =========================================================

elif page == "📊 Analytics":
    st.subheader("Data Analytics")

    if not numeric_columns:
        st.warning("No numeric columns were found in this dataset.")
    else:
        selected_columns = st.multiselect(
            "Choose numeric columns to compare",
            numeric_columns,
            default=numeric_columns[:min(2, len(numeric_columns))]
        )

        if selected_columns:
            st.subheader("Summary Statistics")
            st.dataframe(
                data[selected_columns].describe().T,
                use_container_width=True
            )

            st.subheader("Chart Builder")

            chart_type = st.selectbox(
                "Choose chart type",
                ["Line Chart", "Bar Chart", "Area Chart"]
            )

            chart_data = data[selected_columns].copy()

            for column in selected_columns:
                chart_data[column] = pd.to_numeric(
                    chart_data[column], errors="coerce"
                )

            chart_data = chart_data.dropna(how="all").reset_index(drop=True)

            if not chart_data.empty:
                if chart_type == "Line Chart":
                    st.line_chart(chart_data, use_container_width=True)
                elif chart_type == "Bar Chart":
                    st.bar_chart(chart_data, use_container_width=True)
                else:
                    st.area_chart(chart_data, use_container_width=True)

        st.divider()

        st.subheader("Compare Two Columns")

        if len(numeric_columns) >= 2:
            x_column = st.selectbox(
                "First column (X)",
                numeric_columns,
                key="compare_x"
            )

            y_options = [col for col in numeric_columns if col != x_column]

            y_column = st.selectbox(
                "Second column (Y)",
                y_options,
                key="compare_y"
            )

            comparison = data[[x_column, y_column]].copy()
            comparison[x_column] = pd.to_numeric(
                comparison[x_column], errors="coerce"
            )
            comparison[y_column] = pd.to_numeric(
                comparison[y_column], errors="coerce"
            )
            comparison = comparison.dropna()

            if len(comparison) >= 2:
                correlation = comparison[x_column].corr(comparison[y_column])

                st.metric(
                    "Correlation",
                    f"{correlation:.3f}" if pd.notna(correlation) else "Unavailable"
                )

                if pd.notna(correlation):
                    if correlation > 0.5:
                        st.info("These columns have a strong positive relationship.")
                    elif correlation < -0.5:
                        st.info("These columns have a strong negative relationship.")
                    else:
                        st.info("The linear relationship is weak or moderate.")

                st.scatter_chart(
                    comparison,
                    x=x_column,
                    y=y_column,
                    use_container_width=True
                )
            else:
                st.warning("Not enough valid rows to compare these columns.")
        else:
            st.info("At least two numeric columns are required for comparison.")

# =========================================================
# 10. AI ASSISTANT PAGE
# =========================================================

elif page == "🤖 AI Assistant":
    st.subheader("🤖 InsightAI Data Assistant")

    st.write(
        "Ask questions about your uploaded data. "
        "This version answers common questions using Pandas; "
        "it does not require an external AI API."
    )

    with st.form("question_form"):
        question = st.text_input(
            "Ask a question",
            placeholder="Example: What is the average Sales?"
        )

        submitted = st.form_submit_button("Analyze Question")

    if submitted:
        result = answer_question(data, question)
        st.markdown("### Answer")
        st.write(result)

    st.markdown("### Try these questions")

    examples = [
        "How many rows are there?",
        "What are the missing values?",
        "Are there any duplicate rows?",
        "Show the column names",
        "What is the average of Sales?",
        "What is the total of Profit?",
        "What is the highest value of Revenue?"
    ]

    for example in examples:
        st.markdown(f"- {example}")

    st.caption(
        "Tip: Use the exact column name from your dataset in your question."
    )

# =========================================================
# 11. FORECAST PAGE
# =========================================================

elif page == "🔮 Forecast":
    st.subheader("Simple Trend Forecast")

    st.warning(
        "This is a basic linear-trend estimate, not a fully trained "
        "machine-learning forecasting model. Results depend on the "
        "order and quality of your data."
    )

    if not numeric_columns:
        st.warning("No numeric columns are available for forecasting.")
    else:
        forecast_column = st.selectbox(
            "Select a column to forecast",
            numeric_columns
        )

        periods = st.slider(
            "Number of future points",
            min_value=1,
            max_value=12,
            value=3
        )

        if st.button("Generate Forecast"):
            forecast = make_forecast(data[forecast_column], periods)

            if forecast is None:
                st.error(
                    "At least two valid numeric observations are needed."
                )
            else:
                st.subheader("Forecast Results")
                st.dataframe(forecast, use_container_width=True, hide_index=True)

                history = pd.to_numeric(
                    data[forecast_column], errors="coerce"
                ).dropna().reset_index(drop=True)

                history_frame = pd.DataFrame({
                    "Observation": range(1, len(history) + 1),
                    "Actual": history
                })

                st.subheader("Historical Values")
                st.line_chart(
                    history_frame.set_index("Observation"),
                    use_container_width=True
                )

                st.caption(
                    "Forecast values are estimates and should not be treated "
                    "as guaranteed future outcomes."
                )

# =========================================================
# 12. DATA QUALITY PAGE
# =========================================================

elif page == "🧹 Data Quality":
    st.subheader("Data Quality Report")

    missing_by_column = data.isna().sum()
    missing_report = pd.DataFrame({
        "Column": missing_by_column.index.astype(str),
        "Missing Values": missing_by_column.values,
        "Missing Percentage": (
            missing_by_column.values / max(len(data), 1) * 100
        ).round(2)
    })

    duplicate_count = int(data.duplicated().sum())

    q1, q2, q3 = st.columns(3)
    q1.metric("Rows", f"{len(data):,}")
    q2.metric("Missing Cells", f"{int(missing_by_column.sum()):,}")
    q3.metric("Duplicate Rows", f"{duplicate_count:,}")

    st.subheader("Missing Values by Column")
    st.dataframe(missing_report, use_container_width=True, hide_index=True)

    st.subheader("Duplicate Rows")

    if duplicate_count > 0:
        st.dataframe(
            data[data.duplicated(keep=False)].head(100),
            use_container_width=True
        )
    else:
        st.success("No duplicate rows found.")

    st.divider()

    st.subheader("Optional Data Cleaning")

    remove_duplicates = st.checkbox("Remove duplicate rows")
    fill_missing = st.checkbox("Fill missing numeric values with column averages")

    if st.button("Create Cleaned Dataset"):
        cleaned = data.copy()

        if remove_duplicates:
            cleaned = cleaned.drop_duplicates()

        if fill_missing:
            clean_numeric = get_numeric_columns(cleaned)
            for column in clean_numeric:
                average = cleaned[column].mean()
                if pd.notna(average):
                    cleaned[column] = cleaned[column].fillna(average)

        st.success("A cleaned copy has been created. Your original upload is unchanged.")
        st.write(f"Original rows: {len(data):,}")
        st.write(f"Cleaned rows: {len(cleaned):,}")
        st.write(f"Remaining missing cells: {int(cleaned.isna().sum().sum()):,}")

        st.dataframe(cleaned.head(20), use_container_width=True)

        st.download_button(
            "⬇️ Download Cleaned Dataset",
            data=cleaned.to_csv(index=False).encode("utf-8"),
            file_name="insightai_cleaned_dataset.csv",
            mime="text/csv"
        )

# =========================================================
# 13. FOOTER
# =========================================================

st.divider()
st.caption("InsightAI | Business Data Analysis Dashboard")
