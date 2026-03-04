import numpy as np
from cfg.robot_config import (
    CMD_MODE_NORMAL, CMD_MODE_MIT,
    CONTROL_PARAMS,
)
from effector import create_effector_state


class ArmState:

    def __init__(self, num_joints: int, joint_limits: list,
                 effector_type: str = None, effector_params: dict = None):
        self.num_joints   = num_joints
        self.joint_limits = joint_limits

        # Kinematic state
        self.joint_angles   = np.zeros(num_joints)
        self.tcp_xyz_wxyz   = np.zeros(7)
        self.tcp_xyz_rpy    = np.zeros(6)
        self.flange_xyz_rpy = np.zeros(6)

        # Effector
        self.effector_type = effector_type
        self.effector = create_effector_state(effector_type, effector_params or {})

        # Step sizes
        self.joint_step       = CONTROL_PARAMS["joint_step_rad"]
        self.translation_step = CONTROL_PARAMS["translation_step"]
        self.rotation_step    = CONTROL_PARAMS["rotation_step"]

        # Modes
        self.up_level_mode  = "joint"           # joint | pose
        self.low_level_mode = "joint"           # joint | pose
        self.command_mode   = CMD_MODE_NORMAL   # CMD_MODE_NORMAL | CMD_MODE_MIT

        # Connection
        self.arm_connected = False
        self.arm_enabled   = False

        # Speed
        self._control_speed_factors      = list(CONTROL_PARAMS["control_speed_factors"])
        self._control_speed_factor_index = CONTROL_PARAMS["control_speed_factor_index"]
        self._movement_speeds            = list(CONTROL_PARAMS["movement_speeds"])
        self._movement_speed_index       = CONTROL_PARAMS["movement_speed_index"]

        # Saved positions
        self.saved_positions = []
        self.position_index  = -1
        self.replay_reversed = False


    # Speed factor query

    def get_control_speed_factor(self) -> float:
        """Current velocity scaling factor."""
        return self._control_speed_factors[self._control_speed_factor_index]

    def get_movement_speed(self) -> int:
        """Current speed percentage."""
        return self._movement_speeds[self._movement_speed_index]

    # Joint limits

    def clamp_joints(self):
        """Clip every joint angle to its ``[lower, upper]`` limit."""
        for i in range(self.num_joints):
            lower, upper = self.joint_limits[i]
            if self.joint_angles[i] < lower or self.joint_angles[i] > upper:
                print(f"Warning: Joint {i+1} clamped "
                      f"({self.joint_angles[i]} → {lower, upper})")
            self.joint_angles[i] = np.clip(self.joint_angles[i], lower, upper)

    # Mode toggles

    def toggle_up_level_mode(self):
        self.up_level_mode = "pose" if self.up_level_mode == "joint" else "joint"

    def toggle_low_level_mode(self):
        self.low_level_mode = "pose" if self.low_level_mode == "joint" else "joint"

    def toggle_command_mode(self):
        self.command_mode = (
            CMD_MODE_MIT if self.command_mode == CMD_MODE_NORMAL
            else CMD_MODE_NORMAL
        )

    # Speed cycling

    def cycle_control_speed_factor(self, direction: int):
        """Cycle control_speed factor: ``+1`` = faster, ``-1`` = slower."""
        self._control_speed_factor_index = (
            (self._control_speed_factor_index + direction)
            % len(self._control_speed_factors)
        )

    def cycle_movement_speed(self, direction: int):
        """Cycle movement speed: ``+1`` = faster, ``-1`` = slower."""
        self._movement_speed_index = (
            (self._movement_speed_index + direction)
            % len(self._movement_speeds)
        )

    # Effector update

    def update_effector(self, delta: float):
        """Update effector state based on input delta."""
        self.effector.update(delta, self.get_control_speed_factor())

    # Effector state snapshot (for save/restore & display)

    def get_effector_state(self) -> dict:
        """Return a serialisable snapshot of current effector state."""
        return self.effector.get_state()

    def _restore_effector_state(self, state: dict):
        """Restore effector state from a snapshot dictionary."""
        self.effector.restore_state(state)

    # Position saving / restoring

    def save_position(self):
        """Save current joint angles + effector state."""
        self.saved_positions.append({
            "joints":   self.joint_angles.copy(),
            "effector": self.get_effector_state(),
        })
        self.position_index = len(self.saved_positions) - 1

    def clear_current_position(self):
        """Remove the currently selected saved position."""
        if 0 <= self.position_index < len(self.saved_positions):
            self.saved_positions.pop(self.position_index)
            self.position_index = min(
                self.position_index, len(self.saved_positions) - 1,
            )

    def clear_all_positions(self):
        """Delete every saved position."""
        self.saved_positions.clear()
        self.position_index = -1

    def toggle_replay_order(self):
        self.replay_reversed = not self.replay_reversed

    def restore_next_position(self) -> bool:
        """Move to the next saved position. Returns ``True`` on success."""
        if not self.saved_positions:
            return False
        n = len(self.saved_positions)
        step = -1 if self.replay_reversed else 1
        self.position_index = (self.position_index + step) % n
        pos = self.saved_positions[self.position_index]
        self.joint_angles = pos["joints"].copy()
        self._restore_effector_state(pos.get("effector", {}))
        return True
