import pandas as pd


class DataSummary:

    @staticmethod
    def get_summary(df, uploaded_file=None):
        """Return overall dataset summary."""

        summary = {}

        summary["rows"] = df.shape[0]
        summary["columns"] = df.shape[1]

        summary["numeric"] = len(
            df.select_dtypes(include=["number"]).columns
        )

        summary["categorical"] = len(
            df.select_dtypes(exclude=["number"]).columns
        )

        summary["memory"] = round(
            df.memory_usage(deep=True).sum() / (1024 ** 2),
            2
        )

        if uploaded_file is not None:
            summary["file_size"] = round(
                uploaded_file.size / (1024 ** 2),
                2
            )
        else:
            summary["file_size"] = None

        return summary

    @staticmethod
    def variable_summary(df):
        """Return variable level summary."""

        table = pd.DataFrame({
            "Variable": df.columns,
            "Data Type": df.dtypes.astype(str),
            "Missing Values": df.isnull().sum().values,
            "Missing %": (
                (df.isnull().sum() / len(df)) * 100
            ).round(2).values,
            "Unique Values": df.nunique(dropna=False).values
        })

        return table