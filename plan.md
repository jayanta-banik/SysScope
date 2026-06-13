# SysScope v1.0 Implementation Plan

## Product Decisions

- Ship a native PySide6 desktop application for Windows 10+ and desktop Linux.
- Treat WSL as a selectable data source from the Windows build only; never run
  GUI components or install a SysScope agent inside WSL.
- Show the local clock by default. A running or paused stopwatch/timer replaces
  it; reset restores the clock. Starting one timekeeping mode ends the other.
- Use one built-in dark futuristic HUD theme, JSON configuration, and
  single-file PyInstaller distributions.
- Keep remote monitoring, browser UI, networking, disk/process monitoring,
  controls, alerts, plugins, databases, and additional themes out of v1.0.

## Architecture And Interfaces

- Organize `src/sysscope` into configuration, immutable metric models,
  timekeeping, collectors, worker-thread orchestration, history, and PySide6 UI.
- Normalize every source into one `MetricSnapshot` containing a Unix timestamp,
  source ID, `CpuMetrics`, `MemoryMetrics`, and zero or more indexed
  `GpuMetrics`. UI code consumes snapshots and never source-specific output.
- Give each collector the same lifecycle: `sample() -> MetricSnapshot`,
  `stop() -> None`, and a `paced` flag indicating whether the source controls
  its own sample interval.
- Use psutil and pynvml for native host collection. Missing NVML, missing
  drivers, or no NVIDIA GPUs produces an empty GPU list while CPU/RAM continue.
- On Windows, discover distributions with `wsl.exe --list --quiet`. Launch one
  persistent `wsl.exe -d <distribution> -- python3 -u -c <probe>` process for
  the selected WSL source. The embedded probe reads `/proc/stat`,
  `/proc/meminfo`, and `nvidia-smi`, then writes one JSON record per interval.
- Run the active collector in one dedicated Qt thread. Publish snapshots,
  source errors, and WSL-fallback requests through Qt signals. Stop and join the
  old worker before switching source or exiting.
- Store 60 seconds of CPU, RAM, per-GPU utilization, and per-GPU memory
  percentage in bounded deques sized from the configured refresh interval.
- Use monotonic time for stopwatch/timer calculations and wall-clock time only
  for the local clock display.

## UI, Configuration, And Behavior

- Build a frameless, draggable, edge-resizable, always-on-top HUD. Exclude
  buttons and input controls from drag-anywhere behavior.
- Compact mode shows the clock or active session, CPU, RAM, and one card per
  GPU. Expanded mode adds non-interactive auto-scrolling graphs and the GC
  action/result.
- Put Compact/Expanded, Start Stopwatch, Start Timer, Pause/Resume, Reset,
  source selection, and Exit in the widget right-click menu. Show inline
  Pause/Resume and Reset controls only during an active timekeeping session.
- Keep the clock visible while the timer-duration dialog is open. A finished
  timer remains visible at `00:00:00` until reset; v1.0 emits no alert.
- Close the window to the tray. The tray menu contains Show SysScope,
  Hide SysScope, and Exit SysScope. Explicit exit stops the collector first.
- Read and write `config.json` beside a frozen executable and in the current
  directory during development. Validate fields independently and use defaults
  for missing, malformed, or unsupported values.
- Defaults: always-on-top enabled, start-minimized disabled, compact mode,
  24-hour clock, 1000 ms refresh, 60-second history, native-host source,
  `dark_futuristic_hud` theme, and a 420 by 300 window.
- Persist display mode, clock format, refresh interval, history length, source,
  window settings, and theme. If a selected WSL source fails, display the error,
  switch to the host source, and persist the fallback.

## Delivery And Acceptance

- Package with `pyinstaller --clean --noconfirm SysScope.spec`. PyInstaller must
  run natively on Windows to produce `SysScope.exe` and natively on Linux to
  produce `SysScope`; builds are not cross-compiled.
- Run pytest and pytest-qt on Windows and Linux through GitHub Actions using
  offscreen Qt where needed. CI mocks NVML and WSL; physical GPU/WSL behavior is
  a documented manual release gate.
- Accept FR-001 through FR-006 and UI-001 through UI-004 only when their mapped
  automated tests or manual release checks in `task.md` pass.
- Before release, verify native multi-GPU and Windows-to-WSL collection,
  graceful no-GPU/source failure behavior, startup under 3 seconds, idle CPU
  under 1%, and normal memory usage under 200 MB.
