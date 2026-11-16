
import pandas as pd


def generate_business_insights(data):

    insights = []

    if data.empty:
        return ["The dataset is empty."]

    numeric_data = data.select_dtypes(include="number")

    # 1. Dataset overview
    insights.append(
        f"Your dataset contains {len(data)} rows "
        f"and {len(data.columns)} columns."
    )

    # 2. Missing values
    missing_count = int(data.isna().sum().sum())

    if missing_count > 0:
        insights.append(
            f"The dataset contains {missing_count} missing cells. "
            "Consider cleaning these values."
        )
    else:
        insights.append(
            "There are no missing values in the dataset."
        )

    # 3. Duplicate records
    duplicate_count = int(data.duplicated().sum())

    if duplicate_count > 0:
        insights.append(
            f"{duplicate_count} duplicate rows were detected."
        )
    else:
        insights.append(
            "No duplicate rows were detected."
        )

    # 4. Numeric column analysis
    for column in numeric_data.columns:

        series = numeric_data[column].dropna()

        if series.empty:
            continue

        average = series.mean()
        maximum = series.max()
        minimum = series.min()

        insights.append(
            f"{column}: Average is {average:,.2f}, "
            f"maximum is {maximum:,.2f}, "
            f"and minimum is {minimum:,.2f}."
        )

    # 5. Highest and lowest average numeric columns
    if len(numeric_data.columns) >= 2:

        averages = numeric_data.mean()

        highest_column = averages.idxmax()
        lowest_column = averages.idxmin()

        insights.append(
            f"{highest_column} has the highest numerical average "
            f"({averages[highest_column]:,.2f}) among numeric columns."
        )

        insights.append(
            f"{lowest_column} has the lowest numerical average "
            f"({averages[lowest_column]:,.2f}) among numeric columns."
        )

    # 6. Correlation analysis
    if len(numeric_data.columns) >= 2:

        correlation = numeric_data.corr()

        pairs = []

        columns = list(correlation.columns)

        for i in range(len(columns)):
            for j in range(i + 1, len(columns)):

                value = correlation.iloc[i, j]

                if pd.notna(value):
                    pairs.append(
                        (columns[i], columns[j], value)
                    )

        if pairs:

            strongest_pair = max(
                pairs,
                key=lambda item: abs(item[2])
            )

            col1, col2, value = strongest_pair

            insights.append(
                f"The strongest correlation is between "
                f"{col1} and {col2}, with a correlation "
                f"of {value:.2f}."
            )

    # 7. Categorical analysis
    categorical_columns = data.select_dtypes(
        include=["object", "category", "string"]
    ).columns

    for column in categorical_columns:

        counts = data[column].dropna().value_counts()

        if not counts.empty:

            top_category = counts.index[0]
            top_count = counts.iloc[0]

            insights.append(
                f"In {column}, '{top_category}' appears most frequently "
                f"with {top_count} records."
            )

    return insights
