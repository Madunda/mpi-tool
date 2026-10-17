import ast
import operator
import numpy as np
import pandas as pd


class DeprivationEngine:
    """
    Production Deprivation Engine

    Responsible for converting Indicator Rules
    into binary deprivation vectors.

    Output:

        1 = Deprived

        0 = Non-deprived

        NaN = Missing
    """

    # ==========================================================
    # Supported Operators
    # ==========================================================

    OPERATORS = {

        ">": operator.gt,

        ">=": operator.ge,

        "<": operator.lt,

        "<=": operator.le,

        "==": operator.eq,

        "!=": operator.ne

    }

    # ==========================================================
    # Rule Types
    # ==========================================================

    RULE_SINGLE = "single"

    RULE_MULTIPLE = "multiple"

    RULE_FORMULA = "formula"

    RULE_COMPOSITE = "composite"

    # ==========================================================
    # Missing Strategies
    # ==========================================================

    MISSING_KEEP = "Keep Missing"

    MISSING_DEPRIVED = "Treat Missing as Deprived"

    MISSING_NON_DEPRIVED = "Treat Missing as Non-Deprived"

    MISSING_IGNORE_STRUCTURAL = "Ignore Structural Missing"

    MISSING_IGNORE_FALSE = "Ignore False Missing"

    # ==========================================================
    # Aggregation Functions
    # ==========================================================

    AGGREGATION_FUNCTIONS = [

        "None",

        "max",

        "min",

        "sum",

        "mean",

        "rowtotal",

        "count"

    ]

    # ==========================================================
    # Main Entry
    # ==========================================================

    @staticmethod
    def evaluate(df, rule):

        rule_type = rule.get("type")

        if rule_type == DeprivationEngine.RULE_SINGLE:

            result = DeprivationEngine._single(df, rule)

        elif rule_type == DeprivationEngine.RULE_MULTIPLE:

            result = DeprivationEngine._multiple(df, rule)

        elif rule_type == DeprivationEngine.RULE_FORMULA:

            result = DeprivationEngine._formula(df, rule)

        elif rule_type == DeprivationEngine.RULE_COMPOSITE:

            result = DeprivationEngine._composite(df, rule)

        else:

            raise ValueError(

                f"Unsupported rule type: {rule_type}"

            )

        result = DeprivationEngine.apply_missing(

            result,

            rule

        )

        return result.astype(float)

    # ==========================================================
    # Validate Rule
    # ==========================================================

    @staticmethod
    def validate(df, rule):

        if "type" not in rule:

            raise ValueError(

                "Rule type missing."

            )

        if rule["type"] == "single":

            if len(rule["conditions"]) != 1:

                raise ValueError(

                    "Single rule requires one condition."

                )

        for cond in rule.get(

            "conditions",

            []

        ):

            if cond["variable"] not in df.columns:

                raise ValueError(

                    f"{cond['variable']} not found."

                )

        return True

    # ==========================================================
    # Missing Handler
    # ==========================================================

    @staticmethod
    def apply_missing(

        result,

        rule

    ):

        strategy = rule.get(

            "missing",

            DeprivationEngine.MISSING_KEEP

        )

        result = result.copy()

        if strategy == DeprivationEngine.MISSING_KEEP:

            return result

        if strategy == DeprivationEngine.MISSING_DEPRIVED:

            result[result.isna()] = 1

            return result

        if strategy == DeprivationEngine.MISSING_NON_DEPRIVED:

            result[result.isna()] = 0

            return result

        if strategy == DeprivationEngine.MISSING_IGNORE_STRUCTURAL:

            return result

        if strategy == DeprivationEngine.MISSING_IGNORE_FALSE:

            return result

        return result

    # ==========================================================
    # Convert Value
    # ==========================================================

    @staticmethod
    def convert(value):

        try:

            return ast.literal_eval(str(value))

        except Exception:

            return value

    # ==========================================================
    # Parse List
    # ==========================================================

    @staticmethod
    def parse_list(value):

        if isinstance(value, list):

            return value

        return [

            DeprivationEngine.convert(x.strip())

            for x in str(value).split(",")

        ]

    # ==========================================================
    # SINGLE RULE
    # ==========================================================

    @staticmethod
    def _single(df, rule):

        condition = rule["conditions"][0]

        variable = condition["variable"]

        operator_name = condition["operator"]

        value = condition["value"]

        series = df[variable]

        result = DeprivationEngine.compare(

            series,

            operator_name,

            value

        )

        result = result.astype(float)

        result[series.isna()] = np.nan

        result = DeprivationEngine.apply_post_rules(df, result, rule)

        return result

    # ==========================================================
    # Comparison Engine
    # ==========================================================

    @staticmethod
    def compare(

        series,

        operator_name,

        value

    ):

        if operator_name in DeprivationEngine.OPERATORS:

            func = DeprivationEngine.OPERATORS[operator_name]

            return func(

                series,

                DeprivationEngine.convert(value)

            )

        if operator_name == "inlist":

            values = DeprivationEngine.parse_list(value)

            return series.isin(values)

        if operator_name == "not inlist":

            values = DeprivationEngine.parse_list(value)

            return ~series.isin(values)

        if operator_name == "between":

            low, high = DeprivationEngine.parse_between(value)

            return (

                (series >= low)

                &

                (series <= high)

            )

        if operator_name == "missing":

            return series.isna()

        if operator_name == "not missing":

            return ~series.isna()

        if operator_name == "contains":

            return series.astype(str).str.contains(

                str(value),

                case=False,

                na=False

            )

        if operator_name == "startswith":

            return series.astype(str).str.startswith(

                str(value),

                na=False

            )

        if operator_name == "endswith":

            return series.astype(str).str.endswith(

                str(value),

                na=False

            )

        raise ValueError(

            f"Unsupported operator: {operator_name}"

        )

    # ==========================================================
    # Parse Between
    # ==========================================================

    @staticmethod
    def parse_between(value):

        if isinstance(value, list):

            return (

                float(value[0]),

                float(value[1])

            )

        values = [

            float(x.strip())

            for x in str(value).split(",")

        ]

        if len(values) != 2:

            raise ValueError(

                "Between requires two values."

            )

        return (

            values[0],

            values[1]

        )

    # ==========================================================
    # Evaluate One Condition
    # ==========================================================

    @staticmethod
    def evaluate_condition(df, condition):

        variable = condition["variable"]
        operator_name = condition["operator"]
        value = condition["value"]

        return DeprivationEngine.compare(
            df[variable],
            operator_name,
            value
        )

    # ==========================================================
    # Apply Post Rules
    # ==========================================================

    @staticmethod
    def apply_post_rules(df, result, rule):

        post_rules = rule.get("post_rules", [])

        if not post_rules:
            return result

        output = result.copy()

        for post in post_rules:

            mask = DeprivationEngine.evaluate_condition(
                df,
                post
            )

            assign = post["assign"]

            if assign == "missing":
                output.loc[mask] = np.nan
            else:
                output.loc[mask] = assign

        return output

    # ==========================================================
    # MULTIPLE RULE
    # ==========================================================

    @staticmethod
    def _multiple(df, rule):

        conditions = rule["conditions"]

        logic = rule.get("logic", "AND").upper()

        if len(conditions) == 0:

            raise ValueError(
                "No conditions were supplied."
            )

        masks = []

        for condition in conditions:

            mask = DeprivationEngine.evaluate_condition(
                df,
                condition
            )

            masks.append(mask)

        result = masks[0]

        for mask in masks[1:]:

            if logic == "AND":
                result = result & mask
            elif logic == "OR":
                result = result | mask
            else:
                raise ValueError(
                    "Logic must be AND or OR."
                )

        result = result.astype(float)

        result = DeprivationEngine.apply_post_rules(
            df,
            result,
            rule
        )

        return result

    # ==========================================================
    # Is Missing
    # ==========================================================

    @staticmethod
    def is_missing(series):

        return series.isna()