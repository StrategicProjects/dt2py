"""dt2 — DataTables v2 for Shiny for Python (anywidget binding)."""

from .options import JS, Options, extensions, register_renderer
from .widget import Dt2, dt2

__all__ = ["Dt2", "dt2", "Options", "JS", "register_renderer", "extensions"]
__version__ = "0.0.1.dev0"
