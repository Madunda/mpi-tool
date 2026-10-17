import pandas as pd


class DataValidator:

    @staticmethod
    def validate(df):

        report = {}

        report["observations"] = len(df)

        report["variables"] = len(df.columns)

        report["duplicate_rows"] = df.duplicated().sum()

        report["missing_cells"] = df.isnull().sum().sum()

        report["constant_variables"] = (
            df.nunique(dropna=False) <= 1
        ).sum()

        report["high_missing_variables"] = (
            ((df.isnull().sum() / len(df)) * 100) > 50
        ).sum()

        return report

    @staticmethod
    def missing_table(df):

        table = pd.DataFrame({

            "Variable": df.columns,

            "Missing Values": df.isnull().sum().values,

            "Missing %": (
                df.isnull().mean() * 100
            ).round(2).values

        })

        return table.sort_values(
            "Missing %",
            ascending=False
        )

    @staticmethod
    def constant_variables(df):

        constant = df.columns[
            df.nunique(dropna=False) <= 1
        ]

        return list(constant)