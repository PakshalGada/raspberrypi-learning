# 🐍 Snake Game with Arduino Joystick

A classic Snake game built with Python and Pygame, featuring Arduino joystick controller support with a keyboard fallback.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Controls](#controls)
- [Project Structure](#project-structure)
- [Game Mechanics](#game-mechanics)

---

## Overview

This is a Python implementation of the classic Snake game that can be controlled using a physical Arduino joystick. If no joystick is connected, the game automatically falls back to keyboard controls. The game includes real-time joystick debug values displayed on screen, making it useful for both gameplay and hardware testing.

---

## Features

-  **Arduino Joystick Support** — Physical joystick control via `ArduinoJoystickController`
-  **Keyboard Fallback** — Automatically switches to arrow keys if joystick is unavailable
-  **Pause & Restart** — Pause mid-game or restart after game over via joystick button or keyboard
-  **Debug Display** — Live joystick X/Y axis and button values shown on screen
-  **Progressive Difficulty** — Snake speeds up slightly each time food is eaten
-  **60 FPS Gameplay** — Smooth rendering with Pygame's clock
-  **Graceful Joystick Handling** — Errors are caught and logged without crashing the game

---

##  Requirements

- Python 3.7+
- Arduino board with a joystick module (analog X/Y + button)
- The following Python packages:

```
pygame
```

- A custom `joystick_controller.py` module providing `ArduinoJoystickController` with:
  - `calibrate()` — Calibrates the joystick on startup
  - `get_direction()` — Returns `'UP'`, `'DOWN'`, `'LEFT'`, `'RIGHT'`, or `None`
  - `is_button_pressed()` — Returns `True` when the joystick button is pressed
  - `get_raw_values()` — Returns a dict `{'x': float, 'y': float, 'button': bool}`
  - `close()` — Releases the serial connection

---

##  Installation

1. **Clone or download** this repository.

2. **Install dependencies:**

```bash
pip install pygame
```

3. **Connect your Arduino joystick** and ensure it is recognized as a serial device.

4. **Place `joystick_controller.py`** in the same directory as `snake_with_joystick.py`. This module handles the serial communication with your Arduino.

---

##  Usage

Run the game from the terminal:

```bash
python snake_with_joystick.py
```

On startup, the game will attempt to connect to the Arduino joystick and calibrate it. If the joystick is not found, it falls back to keyboard controls automatically.

---

##  Controls

| Action | Joystick | Keyboard |
|---|---|---|
| Move snake | Push joystick in direction | Arrow keys |
| Pause / Resume | Press joystick button | `Space` |
| Restart (after Game Over) | Press joystick button | `R` |
| Quit | — | `Esc` |

---

##  Project Structure

```
snake-joystick/
│
├── snake_with_joystick.py     # Main game file
├── joystick_controller.py     # Arduino joystick interface (required)
└── README.md
```

---

##  Game Mechanics

- The snake starts at the center of an **800×600** window on a **20×20 pixel grid**
- **Food** spawns at a random empty grid cell; eating it scores **+10 points**
- The snake **speeds up** slightly with each food eaten (move delay decreases by 2%, capped at 80ms)
- The game ends on **wall collision** or **self-collision**
- The snake cannot reverse direction directly into itself

---

##  Display

| Element | Description |
|---|---|
| 🟩 Green rectangles | Snake body segments |
| 🟥 Red rectangle | Food |
| Score | Top-left corner |
| Joystick status | Shows Connected (green) or Disconnected (red) |
| Debug values | Live X/Y axis and button readings from the joystick |
| Controls hint | Displayed at the bottom of the screen |
