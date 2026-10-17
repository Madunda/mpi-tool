"""Compatibility module for the variable-explorer service.

The application imports :class:`VariableExplorer` from this module.  The
implementation remains in ``variable_explore.py`` so existing code continues
to work as well.
"""

from .variable_explore import VariableExplorer

__all__ = ["VariableExplorer"]
