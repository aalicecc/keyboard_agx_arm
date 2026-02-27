# 键盘遥操机械臂

[English](./README_EN.md)

## 概述

通过键盘在终端/SSH 环境下控制机械臂（支持 PiPER系列、Nero 等）。基于 `pynput` 全局键盘监听，无需图形窗口，同时提供 Viser 网页 3D 可视化。

## 环境要求

- Ubuntu 20.04或更高版本
- Python 3.10 或更高版本，推荐使用 Anaconda 或 Miniconda

## 安装：

1. 安装机械臂Python SDK

   ```bash
   git clone https://github.com/agilexrobotics/pyAgxArm.git
   cd pyAgxArm
   pip3 install .
   ```

2. 克隆本项目并切换至项目根目录下：

   ```bash
   git clone https://github.com/kehuanjack/Gamepad_PiPER.git
   cd Gamepad_PiPER
   ```

3. 安装通用的依赖库和运动学模块的依赖库（任选其一，推荐使用pytracik库）：

   - 基于[pinocchio](https://github.com/stack-of-tasks/pinocchio)库（Python == 3.9）：

      ```bash
      conda create -n test_pinocchio python=3.9.* -y
      conda activate test_pinocchio
      pip3 install -r requirements_common.txt --upgrade
      conda install pinocchio=3.6.0 -c conda-forge
      pip3 install meshcat
      pip3 install casadi
      ```

   - 基于[PyRoKi](https://github.com/chungmin99/pyroki)库（Python >= 3.10）:

      ```bash
      conda create -n test_pyroki python=3.10.* -y
      conda activate test_pyroki
      pip3 install -r requirements_common.txt --upgrade
      pip3 install pyroki@git+https://github.com/chungmin99/pyroki.git@f234516
      ```

   - 基于[cuRobo](https://github.com/NVlabs/curobo)库（Python >= 3.8，推荐的CUDA版本为11.8）:

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

   - 基于[pytracik](https://github.com/chenhaox/pytracik)库（Python >= 3.10）:

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

      
## 使用说明

### 控制虚拟机械臂

> **重要提示：启动前必读**
> 以下启动命令中的参数**必须**根据您的选择的**URDF配置**进行替换：
> - **`arm_type`**：机械臂的型号，示例值 `piper`。
> - **`effector_type`**：末端执行器类型，示例值 `None` 或 `AGX_GRIPPER`。
>
> 注意：使用前，需要在 [robot_config](./cfg/robot_config.py) 选择匹配该机械臂和末端执行器的URDF文件，否则无法在 Viser 网页 3D 可视化。
>
> 当前只有 `piper` 与 `piper_x` 配置了带夹爪和纯机械臂的URDF,其他机械臂暂时只有纯机械臂的URDF

1. 使用默认末端执行器启动(默认末端执行器在[robot_config](./cfg/robot_config.py) 中的 `ROBOT_CONFIGS` 定义)

   ```bash
   python3 main_keyboard_virtual.py --arm_type piper
   ```

2. 使用指定末端执行器启动

   ```bash
   python3 main_keyboard_virtual.py --arm_type piper --effector_type AGX_GRIPPER
   ```

### 控制真实机械臂

> **重要提示：启动前必读**
> 以下启动命令中的参数**必须**根据您的选择的**实际硬件配置**进行替换：
> - **`arm_type`**：机械臂的型号，示例值 `piper`。
> - **`channel`**：机械臂连接的 CAN 端口，示例值 `can0`。
> - **`effector_type`**：末端执行器类型，示例值 `None` 或 `AGX_GRIPPER`。
>
> 注意：使用前，需要在 [robot_config](./cfg/robot_config.py) 选择匹配该机械臂和末端执行器的URDF文件，否则无法在 Viser 网页 3D 可视化。
>
> 当前只有 `piper` 与 `piper_x` 配置了带夹爪和纯机械臂的URDF,其他机械臂暂时只有纯机械臂的URDF

1. **激活 CAN 模块**：

   ```bash
   sudo ip link set can0 up type can bitrate 1000000
   ```

   或使用内置参数：

   ```bash
   python3 main_keyboard.py --arm_type piper --channel can0 --setup-can
   ```

2. **启动控制**：

   ```bash
   python3 main_keyboard.py --arm_type piper --channel can0 --effector_type AGX_GRIPPER
   ```

3. **网页可视化**：打开浏览器访问 `http://localhost:8080` 查看机械臂 3D 状态

## 键盘控制说明

### 功能键映射

| 按键 | 短按功能 | 长按功能 |
|------|----------|----------|
| **空格键** | 连接/断开机械臂 | — |
| **-** | 切换上层控制模式（关节 ↔ 位姿） | 切换底层控制模式（关节 ↔ 位姿） |
| **=** | 切换命令模式（Normal ↔ MIT） | — |
| **1** | 回零位置 | — |
| **2** | 保存当前位置 | 清除当前保存的位置 |
| **3** | 恢复下一个保存的位置 | — |
| **4** | 切换回放顺序（顺序 ↔ 逆序） | 清除所有保存的位置 |
| **Q** | 增加控制速度因子 | 减少控制速度因子 |
| **E** | 增加运动速度 | 减少运动速度 |

### 运动按键

| 按键 | 关节模式功能 | 位姿模式功能 |
|------|--------------|--------------|
| **A / D** | J1 | 末端 X 轴移动 |
| **W / S** | J2 | 末端 Y 轴移动 |
| **Z / X** | J3 | 末端 Z 轴移动 |
| **Y / H** | J4 | 末端绕 X 轴旋转（Roll） |
| **U / J** | J5 | 末端绕 Y 轴旋转（Pitch） |
| **I / K** | J6 | 末端绕 Z 轴旋转（Yaw） |
| **O / L** | J7（仅 Nero） | — |
| **F / G** | 关闭 / 打开夹爪 | 关闭 / 打开夹爪 |

### 控制模式说明

1. **上层模式 (up_level_mode)**：决定键盘轴映射方式
   - `joint`：按键直接驱动各关节
   - `pose`：按键控制末端位姿（笛卡尔空间）

2. **底层模式 (low_level_mode)**：决定发送给机械臂的指令类型
   - `joint`：发送关节角度（move_j / move_js）
   - `pose`：发送末端位姿（move_p）

3. **命令模式 (command_mode)**：
   - `Normal (0x00)`：位置速度模式，平稳运动
   - `MIT (0xAD)`：快速响应模式，低延迟（⚠️ 危险，需保持安全距离）

**⚠️ 重要说明：零位控制须知**

当底层控制模式（low_level_mode）设置为 pose 时，PiPER 系列机械臂在零位（home position）状态下 **必须先将末端执行器抬起**，才能进行正常控制，在使用默认的 `tcp_offset` 时：

- **上层模式为 joint：** 按 `Z` 键抬升 J3 关节，将末端抬起
- **上层模式为 pose：** 按 `A` 键沿 X 轴正向移动，将末端抬起

当底层控制模式（low_level_mode）设置为 pose 时， **仅当机械臂当前位姿接近零位时** ，才能成功执行归零位（home）操作。

**💡 原因：** 零位时机械臂处于折叠状态，若直接进行位姿控制可能导致奇异点问题或自碰撞。

### 速度控制

- **控制速度因子**：0.25× / 0.5× / 1.0×（通过 Q 键循环切换），影响每次按键的步进量
- **运动速度**：10% ~ 100%（通过 E 键循环切换），影响实体机械臂运动速度

### 位置保存

- 可保存多个位置点（关节角度 + 夹爪状态）
- 支持顺序和逆序回放
- 按 **2** 保存，按 **3** 恢复，按 **4** 切换回放方向

## 注意事项

- 建议先运行 `main_keyboard_virtual.py` 进行虚拟测试
- 初次使用建议从低速模式（0.25×）开始，熟悉后再提高
- 机械臂运行期间请保持安全距离
- 数值解在接近奇异点时可能出现关节跳动，请注意安全
- **MIT 快速响应模式（0xAD）危险，请谨慎使用**
- 长按阈值为 0.5 秒
