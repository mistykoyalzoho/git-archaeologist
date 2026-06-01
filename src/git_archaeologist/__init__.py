"""git-archaeologist: Uncover WHY your code exists using AI-powered git history analysis."""

__version__ = "0.1.0"
__author__ = "git-archaeologist contributors"
__license__ = "MIT"

from .analyzer import CodeAnalyzer
from .models import ArchaeologyResult, CodeTarget

__all__ = ["CodeAnalyzer", "ArchaeologyResult", "CodeTarget"]
