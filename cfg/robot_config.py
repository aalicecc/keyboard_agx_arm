import os
import numpy as np
from typing import Dict, Optional, List

# Command mode constants
CMD_MODE_NORMAL = 0x00
CMD_MODE_MIT    = 0xAD

CONTROL_PARAMS = {
    "joint_step_rad":            0.5 * np.pi / 180.0,   # rad per tick
    "translation_step":          0.001,                 # m per tick
    "rotation_step":             0.5,                   # deg per tick
    "control_speed_factors":     [0.25, 0.5, 1.0],
    "control_speed_factor_index": 2,                    # default ×1.0
    "replay_speeds":             [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
    "replay_speed_index":        9,                     # default 100 %
}

NO_EFFECTOR = {
    "effector_joints":   0,
    "effector_step":     0.0,
}

EFFECTOR_REGISTRY: Dict[str, dict] = {
    "AGX_GRIPPER": {
        "effector_joints":   2,
        "effector_step":     1.0,   # % per tick
        "gripper_max_width": 0.07,  # metres
        "gripper_min":       0.0,
        "gripper_max":       100.0,
    },
}

_PIPER_BASE = {
    "desc_dir":              "piper_description",
    "urdf":                  "piper_description.urdf",
    "num_joints":            6,
    "target_link":           "link6",
    "supported_effectors":   ["AGX_GRIPPER"],
    "default_effector":      "AGX_GRIPPER",
    "supports_mit":          True,
    "tcp_offset":            [0.0, 0.0, 0.14],
    "direction": {
        "joint": (1, -1, 1, 1, 1, 1),
        "pose":  (1, 1, -1, 1, 1, 1),
    },
}

_NERO_BASE = {
    "desc_dir":              "nero_description",
    "urdf":                  "nero_description.urdf",
    "num_joints":            7,
    "target_link":           "link7",
    "supported_effectors":   [],
    "default_effector":      None,
    "supports_mit":          False,
    "tcp_offset":            [0.0, 0.0, 0.0],
    "direction": {
        "joint": (1, 1, 1, 1, 1, 1, 1),
        "pose":  (1, 1, -1, 1, 1, 1),
    },
}

# Unified Configuration for All Robotic Arms

ROBOT_CONFIGS: Dict[str, dict] = {
    "piper":   {**_PIPER_BASE},
    "piper_h": {**_PIPER_BASE},
    "piper_l": {**_PIPER_BASE},
    "piper_x": {**_PIPER_BASE,
                "desc_dir": "piper_x_description",
                "urdf":     "piper_x_description.urdf"},
    "nero": {**_NERO_BASE},
}

# Utility Functions

def _robot_description_base_path() -> str:
    """Return the absolute path to the ``robot_description/`` directory."""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
        "robot_description",
    )


def get_robot_config(robot_type: str) -> dict:
    """Return the full config dict for *robot_type*, or raise ValueError."""
    cfg = ROBOT_CONFIGS.get(robot_type)
    if cfg is None:
        raise ValueError(
            f"Unsupported robot_type '{robot_type}'. "
            f"Supported: {list(ROBOT_CONFIGS.keys())}"
        )
    return cfg


def get_robot_paths(robot_type: str) -> dict:
    """Return resolved filesystem paths for *robot_type*."""
    cfg = get_robot_config(robot_type)
    base = _robot_description_base_path()
    return {
        "urdf_path":   os.path.join(base, cfg["desc_dir"], cfg["urdf"]),
        "mesh_path":   os.path.join(base, cfg["desc_dir"], "meshes"),
        "target_link": cfg["target_link"],
    }


def get_effector_params(effector_name: Optional[str]) -> dict:
    """Look up effector params from the registry. Returns NO_EFFECTOR when *name* is None."""
    if effector_name is None:
        return NO_EFFECTOR
    params = EFFECTOR_REGISTRY.get(effector_name)
    if params is None:
        raise ValueError(
            f"Unknown effector '{effector_name}'. "
            f"Registered: {list(EFFECTOR_REGISTRY.keys())}"
        )
    return params


def resolve_effector(robot_type: str,
                     effector_override: Optional[str] = None) -> tuple:
    """Resolve the effector name and params for a robot.

    Returns ``(effector_name, effector_params)``.
    *effector_override* from CLI takes priority over robot default.
    Validates that the effector is in the robot's supported list.
    """
    cfg = get_robot_config(robot_type)
    eff_name = effector_override or cfg["default_effector"]

    if eff_name is not None and eff_name not in cfg["supported_effectors"]:
        raise ValueError(
            f"Effector '{eff_name}' is not supported by '{robot_type}'. "
            f"Supported: {cfg['supported_effectors']}"
        )
    return eff_name, get_effector_params(eff_name)
