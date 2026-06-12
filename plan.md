# SysScope v1.0 Implementation Plan

## Architecture

- Use a `src/sysscope` package split into typed models, JSON configuration,
  timekeeping, collectors, and PySide6 UI.
- Normalize native and WSL data into immutable metric snapshots.
- Run a selected collector in a dedicated Qt thread and publish snapshots or
  source errors through Qt signals.
- Use psutil and pynvml for native collection. Use an embedded, persistent
  Python probe launched through `wsl.exe` for complete WSL CPU, RAM, and GPU
  metrics without installing files in WSL.
- Keep rolling metric histories in bounded deques and render non-interactive
  PyQtGraph plots only in expanded mode.

## User Experience

- Show the local clock by default. A running or paused stopwatch/timer replaces
  it; reset restores the clock.
- Expose display mode, timekeeping, source selection, and exit through the
  widget context menu.
- Keep stopwatch/timer controls inline only during an active session.
- Close to tray; provide Show, Hide, and Exit tray actions.
- Apply one built-in dark futuristic HUD theme with cyan accents.

## Configuration And Failure Handling

- Read and write `config.json` beside the frozen executable, or in the current
  directory during development.
- Validate each value independently and fall back to defaults for malformed,
  missing, or unsupported values.
- Persist display mode, clock format, refresh interval, window settings, and
  selected source.
- Display unavailable GPU/source states without preventing startup. If a WSL
  source fails, return to the Windows host collector.

## Verification And Delivery

- Unit test configuration, models, timekeeping, history bounds, native
  collection, WSL parsing/discovery, and failure behavior.
- Use pytest-qt for HUD and lifecycle tests in offscreen mode.
- Add Windows and Linux GitHub Actions test jobs without requiring GPU hardware.
- Build single-file Windows and Linux outputs using PyInstaller.
- Manually validate NVIDIA and WSL paths plus startup, CPU, and memory targets
  before release.

