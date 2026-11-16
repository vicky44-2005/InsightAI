
import json
import re
import pandas as pd

from modules.gemini_engine import get_gemini_client, MODEL_NAME


# --------------------------------------------------
# 1. GEMINI QUESTION UNDERSTANDING
# --------------------------------------------------

def understand_question(data, question):

    if data is None or data.empty:
        raise ValueError("The dataset is empty.")

    if not question or not question.strip():
        raise ValueError("Please enter a question.")

    prompt = f"""
You are the question understanding engine of InsightAI.

Understand the user's question in ANY language, including
English, Tamil, Tanglish, Hindi and mixed languages.

Identify the data operation needed.

Available operations:
- summary
- average
- sum
- maximum
- minimum
- count
- top
- bottom
- filter
- missing
- unique
- correlation
- group_sum
- group_average
- unsupported

Return ONLY valid JSON.

JSON format:
{{
  "operation": "average",
  "column": "Sales",
  "group_column": null,
  "limit": 5,
  "filter_operator": null,
  "filter_value": null,
  "language": "Tamil",
  "clarification": null
}}

Rules:
1. Use exact column names from the dataset.
2. Do not invent column names.
3. Understand natural language and informal questions.
4. If a required column is unclear, use unsupported.
5. Never generate Python code or SQL.
6. Choose the most suitable operation.

Dataset columns:
{list(data.columns)}

Dataset data types:
{data.dtypes.to_string()}

User question:
{question}
"""

    client = get_gemini_client()

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config={
            "temperature": 0,
            "max_output_tokens": 500,
            "response_mime_type": "application/json"
        }
    )

    if not response.text:
        raise ValueError("Gemini returned an empty response.")

    result = json.loads(response.text)

    allowed_operations = {
        "summary", "average", "sum", "maximum",
        "minimum", "count", "top", "bottom",
        "filter", "missing", "unique",
        "correlation", "group_sum",
        "group_average", "unsupported"
    }

    if result.get("operation") not in allowed_operations:
        raise ValueError("The requested operation is not supported.")

    return result


# --------------------------------------------------
# 2. FORMAT DATAFRAME AS A MARKDOWN TABLE
# --------------------------------------------------

def format_table(data):

    if data.empty:
        return "No records found."

    headers = "| " + " | ".join(
        str(col) for col in data.columns
    ) + " |"

    separator = "| " + " | ".join(
        ["---"] * len(data.columns)
    ) + " |"

    rows = []

    for _, row in data.iterrows():

        values = []

        for value in row:

            if pd.isna(value):
                value = ""

            value = str(value)
            value = value.replace("|", "\\|")
            value = value.replace("\n", " ")

            values.append(value)

        rows.append("| " + " | ".join(values) + " |")

    return "\n".join([headers, separator] + rows)


# --------------------------------------------------
# 3. HANDLE SIMPLE QUESTIONS WITHOUT GEMINI
# --------------------------------------------------


def handle_simple_question(data, question):

    text = question.lower().strip()

    # Detect language
    is_tamil = any("\u0B80" <= char <= "\u0BFF" for char in text)

    # 1. Show first N records
    patterns = [
        r"\b(?:show\s+me\s+)?(?:the\s+)?(?:top|first)\s+(\d+)\s+(?:records?|rows?)\b",
        r"\b(?:show|display)\s+(\d+)\s+(?:records?|rows?)\b"
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            limit = max(1, min(int(match.group(1)), 50))
            result = data.head(limit)
            return (
                f"Here are the first {len(result)} records:\n\n"
                + format_table(result)
            )

    # 2. Count records
    count_words = [
        "how many rows", "how many records",
        "total records", "number of records",
        "record count", "row count",
        "ethana records", "ethana rows",
        "evlo records", "evlo rows",
        "மொத்த பதிவுகள்", "எத்தனை பதிவுகள்",
        "எத்தனை வரிசைகள்"
    ]

    if any(word in text for word in count_words):
        return f"Total records / மொத்த பதிவுகள்: {len(data):,}"

    # 3. Identify calculation operation
    operation = None

    average_words = [
        "average", "mean", "sarasari", "saraasari",
        "சராசரி", "சராசரியாக"
    ]

    sum_words = [
        "sum", "total", "motham", "மொத்தம்",
        "மொத்த", "கூட்டுத்தொகை"
    ]

    maximum_words = [
        "maximum", "max", "highest", "highest value",
        "largest", "adhigam", "adhigamaana",
        "அதிகபட்சம்", "அதிகமான", "மிக அதிகம்"
    ]

    minimum_words = [
        "minimum", "min", "lowest", "smallest",
        "kuraivu", "kuraindha", "குறைந்தபட்சம்",
        "குறைவான", "மிகக் குறைவு"
    ]

    if any(word in text for word in average_words):
        operation = "average"

    elif any(word in text for word in sum_words):
        operation = "sum"

    elif any(word in text for word in maximum_words):
        operation = "maximum"

    elif any(word in text for word in minimum_words):
        operation = "minimum"

    if operation is None:
        return None

    # 4. Find the dataset column
    normalized_question = re.sub(
        r"[^a-z0-9]+", " ", text
    ).strip()

    matched_column = None

    aliases = {
        "Shares Traded": [
            "shares", "volume", "traded shares",
            "shares traded"
        ],
        "Turnover (₹ Cr)": [
            "turnover", "turnover cr"
        ],
        "Close": ["close", "closing"],
        "Open": ["open", "opening"],
        "High": ["high"],
        "Low": ["low"]
    }

    for col in sorted(data.columns, key=lambda x: len(str(x)), reverse=True):

        normalized_column = re.sub(
            r"[^a-z0-9]+", " ", str(col).lower()
        ).strip()

        if normalized_column:
            pattern = (
                r"(?<![a-z0-9])"
                + re.escape(normalized_column)
                + r"(?![a-z0-9])"
            )

            if re.search(pattern, normalized_question):
                matched_column = col
                break

    # Try common column aliases
    if matched_column is None:

        for col, column_aliases in aliases.items():

            actual_column = next(
                (c for c in data.columns
                 if str(c).lower() == col.lower()),
                None
            )

            if actual_column is None:
                continue

            for alias in column_aliases:

                if re.search(
                    r"(?<![a-z0-9])" + re.escape(alias) +
                    r"(?![a-z0-9])",
                    normalized_question
                ):
                    matched_column = actual_column
                    break

            if matched_column is not None:
                break

    if matched_column is None:
        return None

    # 5. Perform calculation using Pandas
    numeric_data = pd.to_numeric(
        data[matched_column], errors="coerce"
    ).dropna()

    if numeric_data.empty:
        return f"No numeric values found in {matched_column}."

    if operation == "average":
        value = numeric_data.mean()
        label = "சராசரி" if is_tamil else "Average"

    elif operation == "sum":
        value = numeric_data.sum()
        label = "மொத்தம்" if is_tamil else "Total"

    elif operation == "maximum":
        value = numeric_data.max()
        label = "அதிகபட்சம்" if is_tamil else "Maximum"

    else:
        value = numeric_data.min()
        label = "குறைந்தபட்சம்" if is_tamil else "Minimum"

    return f"{label} of {matched_column}: {value:,.2f}"

# --------------------------------------------------
# 4. EXECUTE DATASET OPERATIONS
# --------------------------------------------------

def execute_question(data, intent):

    operation = intent["operation"]
    column = intent.get("column")
    limit = intent.get("limit", 5)

    if operation == "summary":

        return {
            "rows": len(data),
            "columns": len(data.columns),
            "column_names": list(data.columns),
            "missing_values": int(data.isna().sum().sum()),
            "duplicate_rows": int(data.duplicated().sum())
        }

    if operation == "missing":

        return data.isna().sum().to_dict()

    if operation == "count":

        return {"total_records": len(data)}

    if operation in {"average", "sum", "maximum", "minimum"}:

        if column not in data.columns:
            raise ValueError("The requested column was not found.")

        numeric_data = pd.to_numeric(
            data[column],
            errors="coerce"
        ).dropna()

        if numeric_data.empty:
            raise ValueError("This column has no valid numeric values.")

        if operation == "average":
            return {
                "column": column,
                "average": float(numeric_data.mean())
            }

        if operation == "sum":
            return {
                "column": column,
                "sum": float(numeric_data.sum())
            }

        if operation == "maximum":
            return {
                "column": column,
                "maximum": float(numeric_data.max())
            }

        return {
            "column": column,
            "minimum": float(numeric_data.min())
        }

    if operation in {"top", "bottom"}:

        if column not in data.columns:
            raise ValueError("The requested column was not found.")

        limit = max(1, min(int(limit), 50))

        numeric_data = pd.to_numeric(
            data[column],
            errors="coerce"
        )

        valid_rows = data.loc[numeric_data.notna()].copy()
        valid_rows[column] = numeric_data[numeric_data.notna()]

        if operation == "top":

            return valid_rows.nlargest(
                limit, column
            ).to_dict(orient="records")

        return valid_rows.nsmallest(
            limit, column
        ).to_dict(orient="records")

    if operation == "unique":

        if column not in data.columns:
            raise ValueError("The requested column was not found.")

        return {
            "column": column,
            "unique_values": data[column].dropna().unique().tolist()
        }

    if operation == "correlation":

        numeric_data = data.select_dtypes(include="number")

        if numeric_data.shape[1] < 2:
            raise ValueError(
                "At least two numeric columns are required."
            )

        return numeric_data.corr().round(3).to_dict()

    if operation in {"group_sum", "group_average"}:

        group_column = intent.get("group_column")

        if group_column not in data.columns or column not in data.columns:
            raise ValueError("Required columns were not found.")

        numeric_data = pd.to_numeric(
            data[column],
            errors="coerce"
        )

        working_data = data[[group_column]].copy()
        working_data[column] = numeric_data

        if operation == "group_sum":

            result = working_data.groupby(
                group_column
            )[column].sum()

        else:

            result = working_data.groupby(
                group_column
            )[column].mean()

        return result.to_dict()

    if operation == "filter":

        if column not in data.columns:
            raise ValueError("The requested column was not found.")

        operator = intent.get("filter_operator")
        value = intent.get("filter_value")

        if operator not in {
            "greater_than", "less_than", "equals"
        }:
            raise ValueError("The filter condition is unclear.")

        numeric_data = pd.to_numeric(
            data[column],
            errors="coerce"
        )

        try:
            numeric_value = float(value)

        except (TypeError, ValueError):
            raise ValueError("The filter value must be numeric.")

        if operator == "greater_than":
            filtered = data[numeric_data > numeric_value]

        elif operator == "less_than":
            filtered = data[numeric_data < numeric_value]

        else:
            filtered = data[numeric_data == numeric_value]

        return {
            "matching_records": len(filtered),
            "records": filtered.head(50).to_dict(orient="records")
        }

    if operation == "unsupported":

        return {
            "message": intent.get(
                "clarification",
                "This question needs clarification."
            )
        }

    raise ValueError("This question type is not supported yet.")


# --------------------------------------------------
# 5. MAIN QUESTION ANSWERING FUNCTION
# --------------------------------------------------

def answer_question(data, question):

    if data is None or data.empty:
        raise ValueError("The dataset is empty.")

    if not question or not question.strip():
        raise ValueError("Please enter a question.")

    # First try direct Pandas processing

    simple_answer = handle_simple_question(data, question)

    if simple_answer is not None:
        return simple_answer

    # Use Gemini for questions needing language understanding

    intent = understand_question(data, question)

    result = execute_question(data, intent)

    # Explain calculated result using Gemini

    prompt = f"""
You are InsightAI, a multilingual data analyst.

The user asked:
{question}

The detected language is:
{intent.get("language", "the user's language")}

The operation performed:
{intent["operation"]}

The calculated result:
{json.dumps(result, ensure_ascii=False, default=str)}

Explain this result clearly to the user.

Rules:
1. Respond in the same language as the user's question.
2. Support Tamil, Tanglish, Hindi and English.
3. Never change or invent calculated values.
4. Explain what the result means.
5. Present lists clearly.
6. If clarification is required, ask the user.
7. Do not claim to have performed analysis that was not done.
"""

    client = get_gemini_client()

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config={
            "temperature": 0.2,
            "max_output_tokens": 1200
        }
    )

    if not response.text:
        raise ValueError(
            "InsightAI could not generate an explanation."
        )

    return response.text.strip()
