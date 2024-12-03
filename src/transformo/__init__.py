"""
Transformo - The general purpose tool for determining geodetic transformations
"""

from __future__ import annotations

import logging

__version__ = "0.1.0"


# Logging
console_handler = logging.StreamHandler()
logger = logging.getLogger(__name__)
logger.addHandler(console_handler)
logger.setLevel(logging.WARNING)
