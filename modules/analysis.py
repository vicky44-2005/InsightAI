def calculate_total_profit(df):
    return df["Profit"].sum()


def calculate_average_profit(df):
    return df["Profit"].mean()


def calculate_total_rd_spend(df):
    return df["R&D Spend"].sum()


def calculate_total_marketing_spend(df):
    return df["Marketing Spend"].sum()


def calculate_total_administration(df):
    return df["Administration"].sum()


def find_missing_values(df):
    return df.isnull().sum().sum()


def find_duplicate_rows(df):
    return df.duplicated().sum()


def get_data_quality_report(df):
    """Return a summary of the dataset's data quality."""

    report = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "missing_values": int(df.isnull().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "empty_columns": [
            col for col in df.columns if df[col].isnull().all()
        ],
        "numeric_columns": df.select_dtypes(
            include="number"
        ).columns.tolist(),
        "categorical_columns": df.select_dtypes(
            include=["object", "category", "bool"]
        ).columns.tolist(),
    }

    return report


def clean_dataset(df, remove_duplicates=False, fill_missing=False):
    """Return a cleaned copy of the dataset."""

    cleaned_df = df.copy()

    if remove_duplicates:
        cleaned_df = cleaned_df.drop_duplicates()

    if fill_missing:
        for col in cleaned_df.columns:
            if cleaned_df[col].isnull().all():
                continue

            if cleaned_df[col].isnull().any():
                if cleaned_df[col].dtype.kind in "iuf":
                    cleaned_df[col] = cleaned_df[col].fillna(
                        cleaned_df[col].median()
                    )
                else:
                    cleaned_df[col] = cleaned_df[col].fillna(
                        "Unknown"
                    )

    return cleaned_df
