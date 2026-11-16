
from pathlib import Path
from io import BytesIO

import pandas as pd


# =====================================================
# 1. FILE VALIDATION
# =====================================================

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}

MAX_FILE_SIZE_MB = 50


def validate_file(filename, file_size):
    """
    Validate the uploaded filename and file size.

    Args:
        filename: Uploaded file's name.
        file_size: File size in bytes.

    Returns:
        (is_valid, message)
    """
    extension = Path(filename).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        return False, "Unsupported format. Upload CSV or Excel files."

    max_size_bytes = MAX_FILE_SIZE_MB * 1024 * 1024

    if file_size > max_size_bytes:
        return False, "File is too large. Maximum allowed size is 50 MB."

    if file_size == 0:
        return False, "The uploaded file is empty."

    return True, "File validation successful."


# =====================================================
# 2. LOAD DATASET
# =====================================================

def load_dataset(file_bytes, filename):
    """
    Load a CSV or Excel file from bytes.

    Returns:
        pandas DataFrame

    Raises:
        ValueError if the file cannot be loaded or is invalid.
    """
    extension = Path(filename).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError("Only CSV and Excel files are supported.")

    try:
        if extension == ".csv":
            # Try common encodings for CSV files.
            last_error = None

            for encoding in ("utf-8-sig", "utf-8", "cp1252"):
                try:
                    data = pd.read_csv(BytesIO(file_bytes), encoding=encoding)
                    break
                except UnicodeDecodeError as error:
                    last_error = error
            else:
                raise ValueError(
                    "Unable to decode this CSV file. "
                    "Try saving it as UTF-8 CSV."
                ) from last_error

        else:
            data = pd.read_excel(BytesIO(file_bytes))

    except ValueError:
        raise
    except Exception as error:
        raise ValueError(
            "Could not read the file. Check that it is a valid CSV or Excel file."
        ) from error

    if data.empty:
        raise ValueError("The file contains no data rows.")

    if len(data.columns) == 0:
        raise ValueError("No columns were found in the file.")

    if len(data.columns) > 500:
        raise ValueError("The file has too many columns (maximum 500).")

    # Clean column names.
    data.columns = [
        str(column).strip() for column in data.columns
    ]

    if any(not column for column in data.columns):
        raise ValueError(
            "One or more columns have empty names. Rename them and upload again."
        )

    if not data.columns.is_unique:
        raise ValueError(
            "Duplicate column names were found. Rename duplicate columns first."
        )

    return data


# =====================================================
# 3. AUTOMATIC COLUMN TYPE DETECTION
# =====================================================

def detect_column_types(data):
    """
    Classify columns as numeric, date, or categorical.

    This is a basic automatic detection method.
    """
    result = {}

    for column in data.columns:
        series = data[column]

        if pd.api.types.is_bool_dtype(series):
            result[column] = "Boolean"

        elif pd.api.types.is_numeric_dtype(series):
            result[column] = "Numeric"

        elif pd.api.types.is_datetime64_any_dtype(series):
            result[column] = "Date"

        else:
            non_null = series.dropna()

            if len(non_null) > 0:
                converted = pd.to_datetime(
                    non_null,
                    errors="coerce"
                )

                date_ratio = converted.notna().mean()

                if date_ratio >= 0.90:
                    result[column] = "Possible date"
                else:
                    result[column] = "Categorical / Text"
            else:
                result[column] = "Empty"

    return result


# =====================================================
# 4. DATASET SUMMARY
# =====================================================

def get_dataset_summary(data):
    """Return basic information about a dataset."""

    return {
        "rows": int(len(data)),
        "columns": int(len(data.columns)),
        "missing_cells": int(data.isna().sum().sum()),
        "duplicate_rows": int(data.duplicated().sum()),
        "memory_usage_bytes": int(
            data.memory_usage(deep=True).sum()
        ),
    }


# =====================================================
# 5. MISSING VALUE REPORT
# =====================================================

def get_missing_value_report(data):
    """Return missing-value counts and percentages."""

    missing_counts = data.isna().sum()

    report = pd.DataFrame({
        "Column": data.columns.astype(str),
        "Missing Values": missing_counts.values,
        "Missing Percentage": (
            missing_counts.values / max(len(data), 1) * 100
        ).round(2),
    })

    return report


# =====================================================
# 6. DATA QUALITY REPORT
# =====================================================

def get_data_quality_report(data):
    """Return a report for each column."""

    types = detect_column_types(data)

    report = pd.DataFrame({
        "Column": data.columns.astype(str),
        "Detected Type": [
            types[column] for column in data.columns
        ],
        "Data Type": [
            str(data[column].dtype) for column in data.columns
        ],
        "Missing Values": [
            int(data[column].isna().sum())
            for column in data.columns
        ],
        "Unique Values": [
            int(data[column].nunique(dropna=True))
            for column in data.columns
        ],
    })

    return report


# =====================================================
# 7. CLEAN DATASET
# =====================================================

def clean_dataset(
    data,
    remove_duplicates=False,
    fill_numeric_missing=False,
    fill_text_missing=False,
    standardize_column_names=False,
):
    """
    Create a cleaned copy of a dataset.

    The original DataFrame is never modified.

    Numeric missing values:
        Filled with column mean.

    Text missing values:
        Filled with 'Unknown'.

    Outliers are not automatically removed because they may
    represent genuine business transactions.
    """
    cleaned = data.copy()

    if standardize_column_names:
        cleaned.columns = [
            str(column).strip().lower()
            .replace(" ", "_")
            .replace("-", "_")
            for column in cleaned.columns
        ]

        if not cleaned.columns.is_unique:
            raise ValueError(
                "Standardizing column names caused duplicate names. "
                "Please rename the columns manually."
            )

    if remove_duplicates:
        cleaned = cleaned.drop_duplicates().reset_index(drop=True)

    if fill_numeric_missing:
        numeric_columns = cleaned.select_dtypes(
            include="number"
        ).columns

        for column in numeric_columns:
            average = cleaned[column].mean()

            if pd.notna(average):
                cleaned[column] = cleaned[column].fillna(average)

    if fill_text_missing:
        text_columns = cleaned.select_dtypes(
            include=["object", "string", "category"]
        ).columns

        for column in text_columns:
            cleaned[column] = cleaned[column].fillna("Unknown")

    return cleaned


# =====================================================
# 8. EXPORT CLEANED DATA
# =====================================================

def dataset_to_csv_bytes(data):
    """Convert a DataFrame into downloadable CSV bytes."""

    return data.to_csv(index=False).encode("utf-8-sig")
