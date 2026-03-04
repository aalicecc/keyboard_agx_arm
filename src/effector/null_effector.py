from .base import EffectorStateBase
from typing import Optional


class NullEffectorState(EffectorStateBase):

    @property
    def name(self) -> Optional[str]:
        return None

    def update(self, delta: float, speed_factor: float):
        """No-op: no effector to update."""
        pass

    def get_state(self) -> dict:
        """Return empty state dictionary."""
        return {}

    def restore_state(self, state: dict):
        """No-op: no effector state to restore."""
        pass

    def get_viz_params(self) -> tuple:
        """Return zero parameters for visualization."""
        return (0.0, 0.0, 0)

    def get_status_text(self) -> str:
        """Return 'None' status text."""
        return "Effector:     None"

    def get_key_guide(self) -> list[str]:
        """Return empty key guide."""
        return []

