import numpy as np
from .base import EffectorStateBase
from typing import Optional


class AgxGripperState(EffectorStateBase):
    
    @property
    def name(self) -> Optional[str]:
        return "agx_gripper"

    def __init__(self, params: dict):
        """Initialize AGX gripper state from configuration parameters."""
        self.gripper_state     = params["gripper_min"]
        self.gripper_max_width = params["gripper_max_width"]
        self.step              = params["effector_step"]
        self.min_val           = params["gripper_min"]
        self.max_val           = params["gripper_max"]
        self.effector_joints   = params["effector_joints"]

    def update(self, delta: float, speed_factor: float):
        """Update gripper percentage based on input delta and speed factor."""
        self.gripper_state += delta * self.step * speed_factor
        self.gripper_state = float(
            np.clip(self.gripper_state, self.min_val, self.max_val)
        )

    def get_state(self) -> dict:
        """Return gripper state as serializable dictionary."""
        return {"gripper": self.gripper_state}

    def restore_state(self, state: dict):
        """Restore gripper state from snapshot dictionary."""
        self.gripper_state = state.get("gripper", 0.0)

    def get_viz_params(self) -> tuple:
        """Return visualization parameters: (percentage, max_width, urdf_joints)."""
        return (self.gripper_state, self.gripper_max_width, self.effector_joints)

    def get_status_text(self) -> str:
        """Return formatted gripper status text."""
        return f"Gripper:      {self.gripper_state:5.1f}%"

    def get_key_guide(self) -> list[str]:
        """Return key guide lines for gripper control."""
        return ["F/G     Gripper −/+      Gripper −/+"]

