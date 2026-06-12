# SysScope v1.0 Tasks

## Requirements Traceability

- **FR-001:** Clock, stopwatch, and timer with millisecond stopwatch resolution.
- **FR-002:** CPU utilization refreshed every configured interval.
- **FR-003:** RAM used, total, and utilization.
- **FR-004:** Independent utilization, memory, and temperature for every NVIDIA GPU.
- **FR-005:** Non-interactive auto-scrolling 60-second CPU, RAM, GPU, and GPU-memory graphs.
- **FR-006:** GC button runs `gc.collect()` and reports collected objects.
- **UI-001:** Frameless, draggable, resizable, always-on-top window.
- **UI-002:** Single dark futuristic HUD theme.
- **UI-003:** Compact and expanded layouts.
- **UI-004:** Tray Show, Hide, and Exit actions.

## E0 - Project Foundation

- [x] Create package metadata, entry point, ignore rules, and documentation.
- [x] Record goal, architecture, requirements, epics, and acceptance criteria.
- [ ] Add application assets and final release screenshots.

## E1 - Configuration And Models

- [ ] Implement normalized CPU, memory, GPU, and snapshot models.
- [ ] Implement validated JSON defaults and persistence beside the executable.
- [ ] Test missing, malformed, partial, and valid configuration files.

## E2 - Native And WSL Metrics

- [ ] Implement native psutil CPU/RAM and pynvml multi-GPU collection.
- [ ] Implement WSL distribution discovery and embedded persistent probe.
- [ ] Implement source switching, worker lifecycle, error display, and fallback.
- [ ] Test no-GPU, multi-GPU, malformed records, discovery, and source failures.

## E3 - Clock, Stopwatch, Timer, And GC

- [ ] Implement persistent clock and mutually exclusive active time sessions.
- [ ] Implement monotonic stopwatch/timer start, pause, resume, and reset.
- [ ] Implement timer-duration dialog and inline active-session controls.
- [ ] Implement GC action and collected-object result.
- [ ] Test accuracy and all state transitions.

## E4 - HUD Window And Navigation

- [ ] Implement frameless dragging, edge resizing, always-on-top, and theme.
- [ ] Implement compact/expanded layouts and right-click navigation.
- [ ] Test window flags, resizing, drag exclusions, and mode switching.

## E5 - Metric Views And Graphs

- [ ] Implement CPU/RAM/per-GPU cards and unavailable states.
- [ ] Implement bounded 60-second histories and PyQtGraph plots.
- [ ] Test snapshot rendering, multi-GPU independence, and history limits.

## E6 - Tray And Application Lifecycle

- [ ] Implement Show, Hide, Exit, close-to-tray, and start-minimized behavior.
- [ ] Persist display/source selection and stop collectors cleanly.
- [ ] Test tray actions, startup behavior, and shutdown.

## E7 - Packaging And Platform Support

- [ ] Add single-file PyInstaller specification.
- [ ] Add Windows/Linux GitHub Actions tests and build validation.
- [ ] Verify config placement and WSL integration platform gating.

## E8 - Release Validation

- [ ] Run automated tests on Windows and Linux.
- [ ] Manually test native NVIDIA and Windows-to-WSL multi-GPU collection.
- [ ] Measure idle CPU below 1%, memory below 200 MB, and startup below 3 seconds.
- [ ] Verify all FR/UI requirements and explicit exclusions before release.

