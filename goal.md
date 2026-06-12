# SysScope v1.0 Goal

## Product Goal

Deliver a lightweight native desktop monitoring widget that keeps the local
clock and essential workstation resource usage visible without interrupting
development, machine-learning, or general desktop workflows.

## Success Criteria

- Runs as a frameless, draggable, resizable, always-on-top PySide6 widget on
  Windows 10+ and desktop Linux.
- Shows current CPU, RAM, and each NVIDIA GPU independently at a configurable
  refresh interval.
- Lets Windows users switch between native host metrics and discovered WSL
  distributions without running GUI components or installing an agent in WSL.
- Keeps the local clock visible unless a running or paused stopwatch/timer
  session temporarily replaces it.
- Provides compact and expanded HUD modes, 60-second historical graphs, a GC
  trigger, and system-tray lifecycle controls.
- Starts in under 3 seconds and targets less than 1% idle CPU and 200 MB RAM.
- Produces a single-file Windows executable and a single-file Linux executable.

## Constraints

- Python 3.12+, PySide6, psutil, pynvml, PyQtGraph, JSON, and PyInstaller.
- Metrics collection must not block the GUI thread.
- GPU and WSL failures must degrade gracefully.
- Configuration lives beside the executable.

## Exclusions

Remote, network, disk, and process monitoring; controls or alerts; plugins;
browser or web-server components; databases; authentication; cloud/mobile
support; and additional themes are outside SysScope v1.0.

