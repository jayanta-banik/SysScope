# SysScope v1.0 Tasks

## Requirements Traceability

- **FR-001:** Always-visible local clock; mutually exclusive stopwatch and timer
  with start, pause, resume, reset, and millisecond stopwatch resolution.
- **FR-002:** CPU utilization refreshed at the configured interval.
- **FR-003:** RAM used, total, and utilization.
- **FR-004:** Independent utilization, memory, and temperature for every NVIDIA GPU.
- **FR-005:** Non-interactive auto-scrolling 60-second CPU, RAM, GPU-utilization,
  and GPU-memory graphs.
- **FR-006:** GC button runs `gc.collect()` and reports collected objects.
- **UI-001:** Frameless, draggable, resizable, always-on-top window.
- **UI-002:** Single dark futuristic HUD theme.
- **UI-003:** Compact and expanded layouts.
- **UI-004:** Tray Show, Hide, and Exit actions.
- **CFG-001:** Validated `config.json` stored beside the executable.
- **PKG-001:** Native single-file Windows and Linux distributions.

## E0 - Project Foundation

- [x] Create `src/sysscope` package, entry point, dependency metadata, and ignore rules.
- [x] Create `goal.md`, `plan.md`, and requirement-traceable `task.md`.
- [x] Document development, testing, and packaging commands.
- [ ] Add final application icon assets and release screenshots.
- **Tests:** Confirm a clean editable install and `python -m sysscope` entry point.

## E1 - Configuration And Domain Models

- [x] Define immutable CPU, memory, GPU, source, and snapshot models.
- [x] Define defaults for window, clock, refresh, history, source, and theme.
- [x] Load JSON while validating each field independently.
- [x] Save JSON atomically beside the executable or development working directory.
- [x] Test missing, malformed, partially valid, valid, and string-path configurations.

## E2 - Native Metrics

- [x] Collect non-blocking CPU utilization through psutil.
- [x] Collect RAM used, total, and percentage through psutil.
- [x] Initialize and shut down NVML safely.
- [x] Enumerate and normalize every NVIDIA GPU independently.
- [x] Continue CPU/RAM collection when NVML or temperature data is unavailable.
- [x] Test multi-GPU normalization and unavailable-NVML behavior.

## E3 - WSL Metrics And Source Lifecycle

- [x] Discover installed distributions with `wsl.exe --list --quiet`.
- [x] Implement the embedded persistent `/proc` and `nvidia-smi` WSL probe.
- [x] Parse framed JSON records into normalized snapshots.
- [x] Start collection outside the GUI thread and publish snapshots/errors by signal.
- [x] Stop and join the active collector on source switch and exit.
- [x] Fall back to the host source after a WSL source failure.
- [x] Test discovery decoding, valid records, malformed records, and probe shutdown.
- [ ] Test worker-thread error signaling and automatic WSL-to-host fallback.

## E4 - Clock, Stopwatch, Timer, And GC

- [x] Display the configured 12-hour or 24-hour local clock by default.
- [x] Implement monotonic stopwatch start, pause, resume, reset, and millisecond display.
- [x] Implement timer-duration dialog and monotonic countdown.
- [x] Keep running, paused, and completed sessions visible until reset.
- [x] Make stopwatch and timer mutually exclusive and restore the clock on reset.
- [x] Run `gc.collect()` and display the number of collected objects.
- [x] Test timing accuracy, pause/resume, completion, invalid duration, and reset.

## E5 - HUD Window And Navigation

- [x] Implement frameless, always-on-top window flags and HUD theme.
- [x] Implement drag-anywhere behavior with interactive-control exclusions.
- [x] Implement edge resizing and minimum dimensions.
- [x] Implement compact and expanded layout switching.
- [x] Implement right-click display, timekeeping, source, and exit menus.
- [x] Show inline time-session controls only while a session is active.
- [ ] Test window flags, edge selection, drag exclusions, and menu actions.
- [x] Test compact/expanded visibility and clock restoration.

## E6 - Metric Cards, History, And Graphs

- [x] Render CPU and RAM cards from normalized snapshots.
- [x] Create, update, and remove per-GPU cards as hardware changes.
- [x] Render a graceful NVIDIA-unavailable state.
- [x] Maintain bounded 60-second histories from the configured interval.
- [x] Render non-interactive CPU, RAM, per-GPU utilization, and memory graphs.
- [x] Reset histories when switching metric sources.
- [x] Test bounded CPU, RAM, GPU-utilization, and GPU-memory histories.
- [ ] Test dynamic multi-GPU card/graph rendering from snapshots.

## E7 - Tray And Application Lifecycle

- [x] Implement tray icon and Show, Hide, and Exit actions.
- [x] Hide to tray on window close.
- [x] Respect start-minimized configuration.
- [x] Persist display/source/window settings and stop collectors on explicit exit.
- [x] Smoke-test complete offscreen startup and shutdown.
- [ ] Test tray actions, close-to-tray behavior, and start-minimized behavior.

## E8 - Packaging, CI, And Release Validation

- [x] Add one-file PyInstaller specification.
- [x] Add Windows and Linux GitHub Actions test jobs.
- [x] Document that Windows and Linux artifacts require native platform builds.
- [x] Verify Linux/WSL single-file build completes.
- [ ] Verify native Windows build produces `dist\SysScope.exe`.
- [ ] Run automated tests on Windows and Linux CI.
- [x] Manually sample native and WSL multi-GPU collectors.
- [ ] Measure startup under 3 seconds, idle CPU under 1%, and memory under 200 MB.
- [ ] Verify every FR/UI/CFG/PKG requirement and explicit exclusion before release.
