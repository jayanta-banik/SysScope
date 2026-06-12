# SysScope

SysScope is a compact, always-on-top desktop HUD for watching CPU, memory, and
NVIDIA GPU activity while keeping a clock, stopwatch, or timer close at hand.
It runs natively on Windows and Linux. On Windows it can also use a selected WSL
distribution as its complete metrics source.

## Development

```bash
python -m venv .venv
source .venv/bin/activate          # Linux
# .venv\Scripts\activate           # Windows
python -m pip install -e ".[dev]"
python -m sysscope
```

Right-click the widget to change its display mode, start or control a
stopwatch/timer, select a metrics source, or exit. Closing the widget hides it
to the system tray.

## Tests

```bash
QT_QPA_PLATFORM=offscreen pytest
```

## Packaging

```bash
pyinstaller SysScope.spec
```

The generated single-file executable is placed in `dist/`. SysScope writes
`config.json` beside the executable. During source development, it writes the
file in the current working directory.

See [goal.md](goal.md), [plan.md](plan.md), and [task.md](task.md) for the
product definition and implementation traceability.

