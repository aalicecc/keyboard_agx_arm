import os
import numpy as np
from scipy.spatial.transform import Rotation as R

from cfg.robot_config import get_robot_config, resolve_effector
from utility.tcp_offset import TcpOffset
from utility.kinematic_adapter import (
    create_kinematic_adapter, xyzw_to_wxyz, wxyz_to_xyzw,
)
from .keyboard_input import KeyboardInput
from .arm_state import ArmState
from .visualizer import Visualizer


class ArmController:

    def __init__(
        self,
        urdf_path: str,
        mesh_path: str,
        root_name: str,
        target_link: str,
        arm_type: str = "piper",
        ik_backend: str = "trac_ik",
        effector_type: str = None,
    ):
        # Robot configuration
        cfg  = get_robot_config(arm_type)
        dirs = cfg["direction"]

        # Resolve effector
        self.effector_type, effector_params = resolve_effector(
            arm_type, effector_type)

        self.arm_type = arm_type
        self.num_joints = cfg["num_joints"]
        self.joint_dirs = dirs["joint"]
        self.pose_dirs  = dirs["pose"]

        # Composable components
        self.input = KeyboardInput()
        self.kinematic = create_kinematic_adapter(
            ik_backend,
            urdf_path=urdf_path,
            target_link=target_link,
            num_joints=self.num_joints,
        )
        self.state = ArmState(
            self.num_joints,
            self.kinematic.joint_limits,
            effector_type=self.effector_type,
            effector_params=effector_params,
        )
        self.tcp = TcpOffset()
        self.visualizer = Visualizer(urdf_path, mesh_path, root_name)

        # Dispatch
        self._edge_handlers = {
            "connect": self._toggle_connection,
            "command": self._toggle_command_mode,
            "home":    self._home_and_visualize,
            "restore": self._restore_position,
        }
        self._short_handlers = {
            "mode":           self.state.toggle_up_level_mode,
            "save":           self.state.save_position,
            "replay":         self.state.toggle_replay_order,
            "control_speed":  lambda: self.state.cycle_control_speed_factor(+1),
            "movement_speed": lambda: self.state.cycle_movement_speed(+1),
        }
        self._long_handlers = {
            "mode":           self.state.toggle_low_level_mode,
            "save":           self.state.clear_current_position,
            "replay":         self.state.clear_all_positions,
            "control_speed":  lambda: self.state.cycle_control_speed_factor(-1),
            "movement_speed": lambda: self.state.cycle_movement_speed(-1),
        }

        # Compute initial forward kinematics
        self._forward_kinematics()

    # TCP offset
    def set_tcp_offset(self, offset, degrees: bool = True):
        """Set TCP offset and recompute FK."""
        self.tcp.set(offset, degrees)
        self._forward_kinematics()

    # Kinematics helpers
    def _store_tcp_pose(self, xyz: np.ndarray, rot: R):
        """Store tool-tip pose into state.tcp_xyz_wxyz / state.tcp_xyz_rpy."""
        self.state.tcp_xyz_wxyz = np.concatenate(
            (xyz, xyzw_to_wxyz(rot.as_quat())))
        self.state.tcp_xyz_rpy = np.concatenate(
            (xyz, rot.as_euler("xyz", degrees=True)))

    def _store_flange_pose(self, link_xyz: np.ndarray, link_rot: R):
        """Store flange (link) pose into state.flange_xyz_rpy."""
        self.state.flange_xyz_rpy = np.concatenate(
            (link_xyz, link_rot.as_euler("xyz", degrees=True)))

    def _forward_kinematics(self):
        """Run FK, apply TCP offset, store flange + tool-tip poses."""
        try:
            link_xyz, link_rot = self.kinematic.solve_fk(self.state.joint_angles)
            self._store_flange_pose(link_xyz, link_rot)
            tcp_xyz, tcp_rot = self.tcp.apply(link_xyz, link_rot)
            self._store_tcp_pose(tcp_xyz, tcp_rot)
        except Exception as e:
            print(f"FK error: {e}")
            self.state.tcp_xyz_wxyz   = np.zeros(7)
            self.state.tcp_xyz_rpy    = np.zeros(6)
            self.state.flange_xyz_rpy = np.zeros(6)

    def _inverse_kinematics(self, target_xyz, target_rot: R):
        """Run IK (with TCP removal), store flange + tool-tip poses."""
        try:
            link_xyz, link_rot = self.tcp.remove(
                np.asarray(target_xyz, float), target_rot)
            result = self.kinematic.solve_ik(
                link_xyz, link_rot, self.state.joint_angles)
            if result is not None:
                self.state.joint_angles = np.array(result[: self.num_joints])
                self._store_flange_pose(link_xyz, link_rot)
                self._store_tcp_pose(target_xyz, target_rot)
            else:
                print("IK not found — keeping current configuration")
        except Exception as e:
            print(f"IK error: {e}")

    # Visualization
    def _update_visualization(self):
        effector_pct, effector_max_width, effector_urdf_joints = (
            self.state.effector.get_viz_params()
        )
        self.visualizer.update(
            self.state.joint_angles,
            effector_pct,
            effector_max_width,
            effector_urdf_joints,
        )

    # Continuous movement (called every tick)
    def _update_joint_mode(self):
        """Drive individual joints from keyboard axes."""
        step = self.state.joint_step * self.state.get_control_speed_factor()
        moved = False
        for i in range(self.num_joints):
            raw = self.input.axis(i)
            if raw:
                self.state.joint_angles[i] += raw * self.joint_dirs[i] * step
                moved = True
        if moved:
            self.state.clamp_joints()
            self._forward_kinematics()
            self._update_visualization()

    def _update_pose_mode(self):
        """Move end-effector in Cartesian space from keyboard axes."""
        sf = self.state.get_control_speed_factor()
        d_local = np.array([
            self.input.axis(i) * self.pose_dirs[i] for i in range(3)
        ]) * self.state.translation_step * sf
        r_local = np.array([
            self.input.axis(i + 3) * self.pose_dirs[i + 3] for i in range(3)
        ]) * self.state.rotation_step * sf

        if not (np.any(d_local) or np.any(r_local)):
            return

        pos = self.state.tcp_xyz_wxyz[:3]
        rot = R.from_quat(wxyz_to_xyzw(self.state.tcp_xyz_wxyz[3:]))
        new_rot = rot * R.from_euler("xyz", r_local, degrees=True)
        new_pos = pos + rot.apply(d_local)
        self._inverse_kinematics(new_pos, new_rot)
        self._update_visualization()

    def _update_effector(self):
        """Adjust effector from keyboard."""
        delta = self.input.effector_delta(self.effector_type)
        if delta:
            self.state.update_effector(delta)
            self._update_visualization()

    # Overridable hooks (virtual defaults)
    def _go_home(self):
        """Reset joints to zero and recompute FK."""
        self.state.joint_angles = np.zeros(self.num_joints)
        self._forward_kinematics()

    def _connect_and_enable(self):
        """Mark arm as connected and enabled (virtual mode)."""
        self.state.arm_connected = True
        self.state.arm_enabled   = True

    def _disconnect_and_disable(self):
        """Home the arm, then mark disconnected (virtual mode)."""
        self._go_home()
        self.state.arm_enabled   = False
        self.state.arm_connected = False

    def _toggle_command_mode(self):
        """Toggle command mode between CMD_MODE_NORMAL and CMD_MODE_MIT."""
        self.state.toggle_command_mode()

    # Action dispatch
    def _toggle_connection(self):
        if not self.state.arm_connected:
            self._connect_and_enable()
        else:
            self._disconnect_and_disable()
        self._update_visualization()

    def _home_and_visualize(self):
        self._go_home()
        self._update_visualization()

    def _restore_position(self):
        if self.state.restore_next_position():
            self._forward_kinematics()
            self._update_visualization()

    def _dispatch(self, name: str, handlers: dict):
        handler = handlers.get(name)
        if handler:
            handler()

    # Main update
    def update(self):
        """Process one tick: read input → dispatch actions → move arm."""
        # Edge-only keys (fire on press)
        for name in self.input.poll_edge_actions():
            self._dispatch(name, self._edge_handlers)

        # Long-press keys (fire on release)
        for name, is_long in self.input.poll_long_press_actions():
            table = self._long_handlers if is_long else self._short_handlers
            self._dispatch(name, table)

        # Continuous movement + effector
        if self.state.arm_connected and self.state.arm_enabled:
            if self.state.up_level_mode == "joint":
                self._update_joint_mode()
            else:
                self._update_pose_mode()
            self._update_effector()

    # State query / display
    def get_state(self) -> dict:
        s = self.state
        info = {
            "arm_type":             self.arm_type,
            "num_joints":           self.num_joints,
            "effector_type":        self.effector_type,
            "joints":               s.joint_angles.copy(),
            "tcp_xyz_rpy":          s.tcp_xyz_rpy.copy(),
            "control_speed_factor": s.get_control_speed_factor(),
            "movement_speed":       s.get_movement_speed(),
            "arm_connected":        s.arm_connected,
            "arm_enabled":          s.arm_enabled,
            "command_mode":         s.command_mode,
            "up_level_mode":        s.up_level_mode,
            "low_level_mode":       s.low_level_mode,
        }
        info.update(s.get_effector_state())
        return info

    def print_state(self):
        """Clear terminal and display current state + key guide."""
        os.system("cls" if os.name == "nt" else "clear")
        self._print_status_block()
        self._print_key_guide()

    def _print_status_block(self):
        s = self.state
        arm_st = "Connected" if s.arm_connected else "Disconnected"
        en_st  = "Enabled"   if s.arm_enabled   else "Disabled"
        idx    = f"#{s.position_index + 1}" if s.saved_positions else "None"
        order  = "Reversed" if s.replay_reversed else "Sequential"

        print(f"=== Keyboard Arm Control ({self.arm_type}) ===")
        print(f"Joints (deg): {[f'{np.degrees(a):6.1f}' for a in s.joint_angles]}")
        print(f"End pose:     {[f'{v:7.3f}' for v in s.tcp_xyz_rpy]}")

        # Effector status
        print(self.state.effector.get_status_text())

        print(f"Command mode: 0x{s.command_mode:02X}")
        print(f"Up mode:      {s.up_level_mode}")
        print(f"Low mode:     {s.low_level_mode}")
        print(f"Control speed factor: ×{s.get_control_speed_factor()}")
        print(f"Movement speed: {s.get_movement_speed()}%")
        print(f"Arm status:   {arm_st} / {en_st}")
        print(f"Replay:       {order}")
        print(f"Saved pos:    {len(s.saved_positions)}  current: {idx}")

    def _print_key_guide(self):
        print()
        print("── Function Keys (short / long press) ────")
        print("Space       Connect / Disconnect")
        print("-           Up mode  /  Low mode (long)")
        print("=           Command mode (Normal ↔ MIT)")
        print("1           Home")
        print("2           Save pos  /  Clear current (long)")
        print("3           Restore pos")
        print("4           Toggle order  /  Clear all (long)")
        print("Q           Control speed +  /  Control speed − (long)")
        print("E           Movement speed + / Movement speed − (long)")
        print()
        print("── Movement Keys ─────────────────────────")
        print("        Joint mode       Pose mode")
        print("A/D     J1               local X")
        print("W/S     J2               local Y")
        print("Z/X     J3               local Z")
        print("Y/H     J4               Roll")
        print("U/J     J5               Pitch")
        print("I/K     J6               Yaw")
        if self.num_joints >= 7:
            print("O/L     J7               (reserved)")
        for line in self.state.effector.get_key_guide():
            print(line)

    # Cleanup
    def stop(self):
        """Stop the keyboard listener and visualization process."""
        self.input.stop()
        self.visualizer.stop()
