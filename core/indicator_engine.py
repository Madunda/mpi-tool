from __future__ import annotations

import uuid
from typing import Dict, List, Any


class IndicatorEngine:
    """
    Engine responsible for creating, validating and managing
    MPI indicator deprivation rules.
    """

    # ==========================================================
    # Supported Rule Types
    # ==========================================================

    RULE_TYPES = [
        "single",
        "multiple",
        "formula",
        "composite"
    ]

    # ==========================================================
    # Supported Operators
    # ==========================================================

    OPERATORS = [
        ">",
        ">=",
        "<",
        "<=",
        "==",
        "!=",
        "in",
        "not in",
        "between"
    ]

    # ==========================================================
    # Missing Value Strategies
    # ==========================================================

    MISSING_STRATEGIES = [
        "keep",
        "non_deprived",
        "deprived",
        "exclude"
    ]

    # ==========================================================
    # Aggregation Levels
    # ==========================================================

    AGGREGATION_LEVELS = [
        "individual",
        "household"
    ]

    # ==========================================================
    # Create Empty Rule
    # ==========================================================

    @staticmethod
    def create_rule():

        return {

            "type": "single",

            "conditions": [],

            "logic": "AND",

            "formula": "",

            "missing": "keep",

            "aggregation": "household"

        }

    # ==========================================================
    # Create Condition
    # ==========================================================

    @staticmethod
    def create_condition(
        variable="",
        operator="==",
        value=None
    ):

        return {

            "variable": variable,

            "operator": operator,

            "value": value

        }

    # ==========================================================
    # Create Indicator
    # ==========================================================

    @staticmethod
    def create_indicator(

        name,

        variable,

        weight

    ):

        return {

            "id": str(uuid.uuid4()),

            "name": name,

            "variable": variable,

            "weight": weight,

            "rule": IndicatorEngine.create_rule()

        }

    # ==========================================================
    # Validate Rule Type
    # ==========================================================

    @staticmethod
    def validate_rule_type(rule_type):

        return rule_type in IndicatorEngine.RULE_TYPES

    # ==========================================================
    # Validate Operator
    # ==========================================================

    @staticmethod
    def validate_operator(operator):

        return operator in IndicatorEngine.OPERATORS

    # ==========================================================
    # Validate Missing Strategy
    # ==========================================================

    @staticmethod
    def validate_missing(strategy):

        return strategy in IndicatorEngine.MISSING_STRATEGIES

    # ==========================================================
    # Validate Aggregation
    # ==========================================================

    @staticmethod
    def validate_aggregation(level):

        return level in IndicatorEngine.AGGREGATION_LEVELS

    # ==========================================================
    # Validate One Condition
    # ==========================================================

    @staticmethod
    def validate_condition(condition):

        if condition["variable"] == "":
            return False

        if not IndicatorEngine.validate_operator(
            condition["operator"]
        ):
            return False

        return True

    # ==========================================================
    # Validate Entire Rule
    # ==========================================================

    @staticmethod
    def validate_rule(rule):

        if not IndicatorEngine.validate_rule_type(
            rule["type"]
        ):
            return False

        if not IndicatorEngine.validate_missing(
            rule["missing"]
        ):
            return False

        if not IndicatorEngine.validate_aggregation(
            rule["aggregation"]
        ):
            return False

        if rule["type"] == "single":

            if len(rule["conditions"]) != 1:

                return False

        if rule["type"] == "multiple":

            if len(rule["conditions"]) < 2:

                return False

        for condition in rule["conditions"]:

            if not IndicatorEngine.validate_condition(
                condition
            ):

                return False

        return True

    # ==========================================================
    # PREVIEW RULE (human-readable text rendering)
    #
    # NOTE: this is a lightweight, static text preview used by the
    # configuration UI (indicator_cards.py / indicator_rules.py) to
    # show the person what their rule *looks like*. It does NOT
    # execute anything against real data - that is the job of
    # DeprivationEngine (core/deprivation_engine.py), which computes
    # actual 0/1/NaN deprivation flags row by row.
    # ==========================================================

    @staticmethod
    def preview_rule(rule):

        if not rule:
            return "No rule defined."

        rule_type = rule.get("type", "single")

        if rule_type == "single":

            conditions = rule.get("conditions", [])

            if not conditions:
                return "No condition defined."

            condition = conditions[0]

            text = f"{condition['variable']} {condition['operator']} {condition['value']}"

        elif rule_type == "multiple":

            conditions = rule.get("conditions", [])

            if not conditions:
                return "No conditions defined."

            logic = rule.get("logic", "AND")

            parts = [
                f"({c['variable']} {c['operator']} {c['value']})"
                for c in conditions
            ]

            text = f" {logic} ".join(parts)

        elif rule_type == "formula":

            formula = rule.get("formula", "").strip()

            text = formula if formula else "No formula defined."

        elif rule_type == "composite":

            text = "Composite indicators are not yet supported."

        else:

            text = "Unknown rule type."

        missing = rule.get("missing", "keep")
        aggregation = rule.get("aggregation", "household")

        return (
            f"{text}\n\n"
            f"Missing value strategy : {missing}\n"
            f"Aggregation level      : {aggregation}"
        )