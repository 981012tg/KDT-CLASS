"""Minimal torchtext compatibility layer for modern CUDA PyTorch.

This project-local package implements only the APIs used by the course notebook.
It intentionally avoids torchtext's discontinued native extension.
"""

__version__ = "0.18.0+compat"


def disable_torchtext_deprecation_warning():
    """Compatibility no-op matching torchtext 0.18's public helper."""

