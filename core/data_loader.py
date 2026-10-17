import pandas as pd


class DataLoader:

    @staticmethod
    def load_dataset(uploaded_file):

        if uploaded_file is None:
            return None

        filename = uploaded_file.name.lower()

        if filename.endswith(".csv"):

            df = pd.read_csv(uploaded_file)

        elif filename.endswith(".xlsx"):

            df = pd.read_excel(uploaded_file)

        elif filename.endswith(".dta"):

            df = DataLoader._load_stata(uploaded_file)

        else:

            raise ValueError(
                "Unsupported file format."
            )

        return df

    @staticmethod
    def _load_stata(uploaded_file):
        """
        Uses the LOW-LEVEL pandas Stata interface (StataReader) instead
        of the high-level pd.read_stata().

        Why: read_stata() always tries to turn Stata value labels into
        pandas categoricals. If a Stata file reuses the same label text
        for more than one numeric code (non-unique value labels), that
        conversion step raises:

            "Value labels for column X are not unique."

        StataReader lets us read the raw numeric/string codes directly
        (no categorical conversion is ever attempted, so this error
        cannot occur), and read the value-label dictionary separately
        so we don't lose the human-readable labels - they're just kept
        as metadata instead of being baked into the column dtype.
        """

        uploaded_file.seek(0)

        with pd.io.stata.StataReader(uploaded_file) as reader:

            # Raw codes only - categorical conversion is never attempted.
            df = reader.read(convert_categoricals=False)

            variable_labels = DataLoader._safe_call(reader, "variable_labels", {})
            raw_value_labels = DataLoader._safe_call(reader, "value_labels", {})

            # Different pandas versions expose value_labels() differently:
            #   - pandas 3.x: already keyed directly by VARIABLE name,
            #     e.g. {"F2S2_Q8": {1: "Owned", 2: "Rented", ...}}
            #   - older pandas: keyed by the underlying Stata "label set"
            #     name, which may differ from the variable name, requiring
            #     a variable -> label-set lookup (varlist/lbllist).
            # We only trust the older varlist/lbllist attributes when
            # they exist as plain public attributes (some pandas
            # versions expose private getter methods with the same
            # names that are NOT safe to call after read() has already
            # consumed the stream - so those are intentionally ignored).

            variable_value_labels = {}

            if raw_value_labels:

                if set(raw_value_labels.keys()) & set(df.columns):

                    # Already keyed by variable name - use as-is.
                    variable_value_labels = raw_value_labels

                else:

                    varlist = getattr(reader, "varlist", None)
                    lbllist = getattr(reader, "lbllist", None)

                    if varlist is not None and lbllist is not None:

                        for var_name, label_name in zip(varlist, lbllist):

                            if label_name and label_name in raw_value_labels:
                                variable_value_labels[var_name] = raw_value_labels[label_name]

            df.attrs["variable_labels"] = variable_labels
            df.attrs["value_labels"] = variable_value_labels

        return df

    @staticmethod
    def _safe_call(reader, method_name, default):
        """Call an optional StataReader method, tolerating pandas
        version differences where a method may not exist or may fail."""

        method = getattr(reader, method_name, None)

        if method is None:
            return default

        try:
            return method()
        except Exception:
            return default