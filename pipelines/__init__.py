"""
Pipeline setup and execution scripts
"""
from .setup_pipeline import main as setup_pipeline
from .run_pipeline import run_pipeline

__all__ = [
    'setup_pipeline',
    'run_pipeline',
]
