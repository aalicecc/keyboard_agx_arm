from typing import Optional
from .base import EffectorStateBase
from .null_effector import NullEffectorState
from .agx_gripper import AgxGripperState


def create_effector_state(
    effector_type: Optional[str],
    effector_params: dict
) -> EffectorStateBase:
    """Create effector state object based on type."""
    if effector_type == "AGX_GRIPPER":
        return AgxGripperState(effector_params)
    # elif effector_type == "REVO2":
    #     return Revo2State(effector_params)
    return NullEffectorState()


__all__ = [
    "EffectorStateBase",
    "NullEffectorState",
    "AgxGripperState",
    "create_effector_state",
]

