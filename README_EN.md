# Keyboard Teleoperation for Robotic Arms

[中文](./README.md)

## Overview

Control robotic arms (PiPER series, Nero, etc.) via keyboard in terminal/SSH environments. Based on `pynput` global keyboard monitoring, no graphical window required, with Viser web-based 3D visualization support.

## Requirements

- Ubuntu 20.04 or higher
- Python 3.10 or higher, recommended to use Anaconda or Miniconda

## Installation

1. Install the robotic arm Python SDK:

   ```bash
   git clone https://github.com/agilexrobotics/pyAgxArm.git
   cd pyAgxArm
   pip3 install .
   ```

2. Clone the project and navigate to the project root:

   ```bash
   git clone https://github.com/kehuanjack/Gamepad_PiPER.git
   cd Gamepad_PiPER
   ```

3. Install common dependencies and kinematic module dependencies (choose one, pytracik is recommended):

   - Based on [pinocchio](https://github.com/stack-of-tasks/pinocchio) library (Python == 3.9):

      ```bash
      conda create -n test_pinocchio python=3.9.* -y
      conda activate test_pinocchio
      pip3 install -r requirements_common.txt --upgrade
      conda install pinocchio=3.6.0 -c conda-forge
      pip3 install meshcat
      pip3 install casadi
      ```

   - Based on [PyRoKi](https://github.com/chungmin99/pyroki) library (Python >= 3.10):

      ```bash
      conda create -n test_pyroki python=3.10.* -y
      conda activate test_pyroki
      pip3 install -r requirements_common.txt --upgrade
      pip3 install pyroki@git+https://github.com/chungmin99/pyroki.git@f234516
      ```

   - Based on [cuRobo](https://github.com/NVlabs/curobo) library (Python >= 3.8, recommended CUDA version 11.8):

      ```bash
      conda create -n test_curobo python=3.10.* -y
      conda activate test_curobo
      pip3 install -r requirements_common.txt --upgrade
      sudo apt install git-lfs && cd ../
      git clone https://github.com/NVlabs/curobo.git && cd curobo
      pip3 install "numpy<2.0" "torch==2.0.0" pytest lark
      pip3 install -e . --no-build-isolation
      python3 -m pytest .
      cd ../Gamepad_PiPER
      ```

   - Based on [pytracik](https://github.com/chenhaox/pytracik) library (Python >= 3.10):

      ```bash
      conda create -n test_tracik python=3.10.* -y
      conda activate test_tracik
      pip3 install -r requirements_common.txt --upgrade
      git clone https://github.com/chenhaox/pytracik.git
      cd pytracik
      pip install -r requirements.txt
      sudo apt install g++ libboost-all-dev libeigen3-dev liborocos-kdl-dev libnlopt-dev libnlopt-cxx-dev
      python setup_linux.py install --user
      ```

## Usage

### Control Virtual Robotic Arm

> **Important: Read Before Starting**
> The parameters in the following startup commands **must** be replaced according to your selected **URDF configuration**:
> - **`arm_type`**: Robotic arm model, example value `piper`.
> - **`effector_type`**: End-effector type, example value `None` or `AGX_GRIPPER`.
>
> Note: Before use, you need to select a URDF file matching the robotic arm and end-effector in [robot_config](./cfg/robot_config.py), otherwise Viser web 3D visualization will not work.
>
> Currently, only `piper` and `piper_x` have URDF configurations with gripper and arm-only versions. Other robotic arms only have arm-only URDF configurations for now.

1. Start with default end-effector (default end-effector is defined in `ROBOT_CONFIGS` in [robot_config](./cfg/robot_config.py)):

   ```bash
   python3 main_keyboard_virtual.py --arm_type piper
   ```

2. Start with selected end-effector:

   ```bash
   python3 main_keyboard_virtual.py --arm_type piper --effector_type AGX_GRIPPER
   ```

### Control Physical Robotic Arm

> **Important: Read Before Starting**
> The parameters in the following startup commands **must** be replaced according to your selected **physical hardware configuration**:
> - **`arm_type`**: Robotic arm model, example value `piper`.
> - **`channel`**: CAN port connected to the robotic arm, example value `can0`.
> - **`effector_type`**: End-effector type, example value `None` or `AGX_GRIPPER`.
>
> Note: Before use, you need to select a URDF file matching the robotic arm and end-effector in [robot_config](./cfg/robot_config.py), otherwise Viser web 3D visualization will not work.
>
> Currently, only `piper` and `piper_x` have URDF configurations with gripper and arm-only versions. Other robotic arms only have arm-only URDF configurations for now.

1. **Activate CAN module**:

   ```bash
   sudo ip link set can0 up type can bitrate 1000000
   ```

   Or use the built-in parameter:

   ```bash
   python3 main_keyboard.py --arm_type piper --channel can0 --setup-can
   ```

2. **Start control**:

   ```bash
   python3 main_keyboard.py --arm_type piper --channel can0 --effector_type AGX_GRIPPER
   ```

3. **Web visualization**: Open a browser and visit `http://localhost:8080` to view the robotic arm 3D status

## Keyboard Control Guide

### Function Key Mapping

| Key | Short Press | Long Press |
|-----|-------------|------------|
| **Space** | Connect/Disconnect robotic arm | — |
| **-** | Toggle upper-level control mode (joint ↔ pose) | Toggle lower-level control mode (joint ↔ pose) |
| **=** | Toggle command mode (Normal ↔ MIT) | — |
| **1** | Home position | — |
| **2** | Save current position | Clear current saved position |
| **3** | Restore next saved position | — |
| **4** | Toggle replay order (sequential ↔ reverse) | Clear all saved positions |
| **Q** | Increase control speed factor | Decrease control speed factor |
| **E** | Increase movement speed | Decrease movement speed |

### Movement Keys

| Key | Joint Mode Function | Pose Mode Function |
|-----|---------------------|-------------------|
| **A / D** | J1 | End-effector X-axis movement |
| **W / S** | J2 | End-effector Y-axis movement |
| **Z / X** | J3 | End-effector Z-axis movement |
| **Y / H** | J4 | End-effector rotation around X-axis (Roll) |
| **U / J** | J5 | End-effector rotation around Y-axis (Pitch) |
| **I / K** | J6 | End-effector rotation around Z-axis (Yaw) |
| **O / L** | J7 (Nero only) | — |
| **F / G** | Close / Open gripper | Close / Open gripper |

### Control Mode Description

1. **Upper-level mode (up_level_mode)**: Determines keyboard axis mapping
   - `joint`: Keys directly drive individual joints
   - `pose`: Keys control end-effector pose (Cartesian space)

2. **Lower-level mode (low_level_mode)**: Determines command type sent to the robotic arm
   - `joint`: Send joint angles (move_j / move_js)
   - `pose`: Send end-effector pose (move_p)

3. **Command mode (command_mode)**:
   - `Normal (0x00)`: Position-velocity mode, smooth motion
   - `MIT (0xAD)`: Fast response mode, low latency (⚠️ Dangerous, maintain safe distance)

**⚠️ Important: Zero Position Control Notice**

When the **lower-level control mode** (`low_level_mode`) is set to `pose`, PiPER series robotic arms **must lift the end-effector first** before normal control can be established from the home position. When using the default `tcp_offset`:

- **Upper-level mode is `joint`:** Press `Z` to lift joint J3 and raise the end-effector
- **Upper-level mode is `pose`:** Press `A` to move along the positive X-axis and lift the end-effector

When the **lower-level control mode** (`low_level_mode`) is set to `pose`, the home position command **only works reliably when the arm's current pose is already near the zero position**.

**💡 Reason:** At the home position, the arm is in a folded configuration. Direct pose control may cause singularity issues or self-collision.

### Speed Control

- **Control speed factor**: 0.25× / 0.5× / 1.0× (cycle through with Q key), affects step size per key press
- **Movement speed**: 10% ~ 100% (cycle through with E key), affects physical robotic arm movement speed

### Position Saving

- Can save multiple position points (joint angles + gripper state)
- Supports sequential and reverse replay
- Press **2** to save, **3** to restore, **4** to toggle replay direction

## Notes

- It is recommended to run `main_keyboard_virtual.py` for virtual testing first
- For first-time use, start with low-speed mode (0.25×) and increase after familiarization
- Maintain a safe distance during robotic arm operation
- Numerical solutions may cause joint jumps near singular points, please be cautious
- **MIT fast response mode (0xAD) is dangerous, use with caution**
- Long-press threshold is 0.5 seconds

