"""General-purpose helper functions for the MPI application."""


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format a decimal value as a percentage for display."""
    return f"{value * 100:.{decimals}f}%"
