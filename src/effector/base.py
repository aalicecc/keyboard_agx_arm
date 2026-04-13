from abc import ABC, abstractmethod
from typing import Optional


class EffectorStateBase(ABC):
    """Unified interface: base class for all effector state management."""

    @property
    @abstractmethod
    def name(self) -> Optional[str]:
        """Return effector type name or None."""
        pass

    @abstractmethod
    def update(self, delta: float, speed_factor: float):
        """Update effector state based on input delta and speed factor.
        
        Args:
            delta: Input change, typically ±1 from keyboard
            speed_factor: Current control speed factor multiplier
        """
        pass

    @abstractmethod
    def get_state(self) -> dict:
        """Return a serializable snapshot of current effector state.
        
        Returns:
            Dictionary containing effector-specific state variables
        """
        pass

    @abstractmethod
    def restore_state(self, state: dict):
        """Restore effector state from a snapshot dictionary.
        
        Args:
            state: Dictionary containing effector state (from get_state())
        """
        pass

    @abstractmethod
    def get_status_text(self) -> str:
        """Return formatted status text for terminal display.
        
        Returns:
            Formatted string showing current effector status
        """
        pass

    @abstractmethod
    def get_key_guide(self) -> list[str]:
        """Return operation key hints for this effector.
        
        Returns:
            List of strings, each representing one line of key guide
        """
        pass

