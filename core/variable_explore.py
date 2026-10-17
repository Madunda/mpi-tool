import pandas as pd
from typing import Any, Dict, Optional


NUMERIC_DTYPES = {"int64", "float64", "int32", "float32", "uint8", "uint16", "uint32", "uint64"}
CATEGORICAL_DTYPES = {"object", "category"}
BOOLEAN_DTYPES = {"bool"}


class VariableExplorer:

    @staticmethod
    def build_variable_table(df: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "Variable": df.columns.astype(str),
                "Data Type": df.dtypes.astype(str),
                "Missing": df.isna().sum().values,
                "Missing %": (df.isna().mean() * 100).round(2).values,
                "Unique": df.nunique(dropna=False).values,
            }
        )

    @staticmethod
    def filter_variables(
        df: pd.DataFrame,
        dtype_filter: str = "All",
        search: str = "",
    ) -> pd.DataFrame:
        table = VariableExplorer.build_variable_table(df)

        if dtype_filter == "Numeric":
            table = table[table["Data Type"].isin(NUMERIC_DTYPES)]
        elif dtype_filter == "Categorical":
            table = table[table["Data Type"].isin(CATEGORICAL_DTYPES)]
        elif dtype_filter == "Boolean":
            table = table[table["Data Type"].isin(BOOLEAN_DTYPES)]
        elif dtype_filter == "Date":
            table = table[table["Data Type"].str.contains("datetime", case=False, na=False)]

        if search:
            table = table[table["Variable"].str.contains(search, case=False, na=False)]

        return table.reset_index(drop=True)

    @staticmethod
    def numeric_summary(series: pd.Series) -> Dict[str, Any]:
        numeric = pd.to_numeric(series, errors="coerce")

        return {
            "Mean": round(numeric.mean(), 2),
            "Median": round(numeric.median(), 2),
            "Minimum": numeric.min(),
            "Maximum": numeric.max(),
            "Std": round(numeric.std(), 2),
            "Missing": int(series.isna().sum()),
        }

    @staticmethod
    def categorical_summary(series: pd.Series, top_n: int = 10) -> pd.DataFrame:
        return (
            series.value_counts(dropna=False)
            .head(top_n)
            .reset_index()
            .rename(columns={"index": "Value", series.name: "Frequency"})
        )

    @staticmethod
    def variable_details(df: pd.DataFrame, variable_name: str) -> Optional[Dict[str, Any]]:
        if variable_name not in df.columns:
            return None

        series = df[variable_name]
        details: Dict[str, Any] = {
            "Variable": variable_name,
            "Data Type": str(series.dtype),
            "Missing": int(series.isna().sum()),
            "Missing %": round(series.isna().mean() * 100, 2),
            "Unique": int(series.nunique(dropna=False)),
        }

        if pd.api.types.is_numeric_dtype(series):
            details["Summary"] = VariableExplorer.numeric_summary(series)
        elif pd.api.types.is_bool_dtype(series):
            details["Summary"] = {
                "True": int(series.sum()),
                "False": int((~series).sum()),
                "Missing": int(series.isna().sum()),
            }
        elif pd.api.types.is_datetime64_any_dtype(series):
            details["Summary"] = {
                "Min": series.min(),
                "Max": series.max(),
                "Missing": int(series.isna().sum()),
            }
        else:
            details["Summary"] = VariableExplorer.categorical_summary(series)

        return details
