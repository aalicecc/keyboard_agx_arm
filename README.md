# 键盘遥操机械臂——终端下的直观机械臂控制

## 摘要

通过键盘在终端/SSH 环境下直观控制机械臂（支持 PiPER、Nero 等）。基于 `pynput` 全局键盘监听，无需图形窗口，同时提供 Viser 网页 3D 可视化。

## 标签
PiPER机械臂、Nero机械臂、键盘遥操、关节控制、位姿控制、夹爪控制、运动学正逆解

## 支持的机械臂

| 型号 | 关节数 | 夹爪 | MIT模式 |
|------|--------|------|---------|
| piper | 6 | ✅ | ✅ |
| piper_h | 6 | ✅ | ✅ |
| piper_l | 6 | ✅ | ✅ |
| piper_x | 6 | ✅ | ✅ |
| nero | 7 | ❌ | ❌ |

## 项目结构

```
keyboard_agx_arm/
├── cfg/
│   ├── __init__.py
│   └── robot_config.py          # 机器人统一配置 + 控制参数常量
├── robot_description/            # URDF / meshes
├── src/
│   ├── keyboard_agx_arm/
│   │   ├── arm_state.py         # 机械臂运行时状态
│   │   ├── arm_controller.py    # 键盘控制核心逻辑
│   │   ├── keyboard_input.py    # 键盘输入监听与解析
│   │   └── visualizer.py        # Viser 3D 可视化
│   └── utility/
│       ├── tcp_offset.py        # TCP 偏移计算
│       └── kinematic_adapter.py # 运动学后端适配器
├── main_keyboard.py             # 实体机械臂入口
└── main_keyboard_virtual.py     # 虚拟机械臂入口（无需硬件）
```

## 环境配置

- 操作系统：Ubuntu 20.04 或更高版本
- Python 环境：Python 3.10 或更高版本，推荐使用 Anaconda 或 Miniconda

安装依赖：

```bash
pip3 install pynput viser numpy scipy
```

安装运动学后端（推荐 pytracik）：

```bash
git clone https://github.com/chenhaox/pytracik.git
cd pytracik
pip install -r requirements.txt
sudo apt install g++ libboost-all-dev libeigen3-dev liborocos-kdl-dev libnlopt-dev libnlopt-cxx-dev
python setup_linux.py install --user
```

## 执行步骤

### 虚拟模式（无需硬件）

```bash
python3 main_keyboard_virtual.py --robot piper
```

### 实体机械臂

1. **激活 CAN 模块**：

```bash
sudo ip link set can0 up type can bitrate 1000000
```

或使用内置参数：

```bash
python3 main_keyboard.py --robot piper_x --channel can0 --setup-can
```

2. **启动控制**：

```bash
python3 main_keyboard.py --robot piper_x --channel can0
python3 main_keyboard.py --robot nero --channel can0 --effector REVO2
```

3. **网页可视化**：打开浏览器访问 `http://localhost:8080` 查看机械臂 3D 状态

## 键盘控制说明

### 功能键映射

| 按键 | 短按功能 | 长按功能 |
|------|----------|----------|
| **Space** | 连接/断开机械臂 | — |
| **-** | 切换上层控制模式（关节 ↔ 位姿） | 切换底层控制模式（关节 ↔ 位姿） |
| **=** | 切换命令模式（Normal ↔ MIT） | — |
| **1** | 回零位置 | — |
| **2** | 保存当前位置 | 清除当前保存的位置 |
| **3** | 恢复下一个保存的位置 | — |
| **4** | 切换回放顺序（顺序 ↔ 逆序） | 清除所有保存的位置 |
| **Q** | 增加控制速度因子 | 减少控制速度因子 |
| **E** | 增加回放速度 | 减少回放速度 |

### 运动按键

| 按键 | 关节模式功能 | 位姿模式功能 |
|------|--------------|--------------|
| **A / D** | J1（底座旋转） | 末端 X 轴移动 |
| **W / S** | J2（大臂） | 末端 Y 轴移动 |
| **Z / X** | J3（小臂） | 末端 Z 轴移动 |
| **Y / H** | J4（腕部偏航） | 末端绕 X 轴旋转（Roll） |
| **U / J** | J5（腕部俯仰） | 末端绕 Y 轴旋转（Pitch） |
| **I / K** | J6（腕部旋转） | 末端绕 Z 轴旋转（Yaw） |
| **O / L** | J7（仅 Nero） | — |
| **F / G** | 关闭 / 打开夹爪 | 关闭 / 打开夹爪 |

### 控制模式说明

1. **上层模式 (up_level_mode)**：决定键盘轴映射方式
   - `joint`：按键直接驱动各关节
   - `pose`：按键控制末端位姿（笛卡尔空间）

2. **底层模式 (low_level_mode)**：决定发送给硬件的指令类型
   - `joint`：发送关节角度（move_j / move_js）
   - `pose`：发送末端位姿（move_p）

3. **命令模式 (command_mode)**：
   - `Normal (0x00)`：位置速度模式，平稳运动
   - `MIT (0xAD)`：快速响应模式，低延迟（⚠️ 危险，需保持安全距离）

### 速度控制

- **控制速度因子**：0.25× / 0.5× / 1.0×（通过 Q 键循环切换），影响每次按键的步进量
- **回放速度**：10% ~ 100%（通过 E 键循环切换），影响实体机械臂运动速度

### 位置记忆

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
