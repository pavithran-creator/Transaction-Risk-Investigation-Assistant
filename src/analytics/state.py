"""
In-memory state management for loaded transaction datasets.
"""

from typing import Optional
from src.models.transaction import TransactionDataset

_CURRENT_DATASET: Optional[TransactionDataset] = None


def get_current_dataset() -> Optional[TransactionDataset]:
    """Retrieve the currently loaded in-memory transaction dataset."""
    return _CURRENT_DATASET


def set_current_dataset(dataset: Optional[TransactionDataset]) -> None:
    """Set the active in-memory transaction dataset."""
    global _CURRENT_DATASET
    _CURRENT_DATASET = dataset


def clear_current_dataset() -> None:
    """Clear the active in-memory transaction dataset."""
    global _CURRENT_DATASET
    _CURRENT_DATASET = None
