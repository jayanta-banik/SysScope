# SysScope

SysScope is a compact, always-on-top desktop HUD for watching CPU, memory, and
NVIDIA GPU activity while keeping a clock, stopwatch, or timer close at hand.
It runs natively on Windows and Linux. On Windows it can also use a selected WSL
distribution as its complete metrics source.

## Running SysScope

### Windows

Run SysScope from native Windows PowerShell, not from inside WSL. Python 3.12+
is required when running from source.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m sysscope
```

To run a packaged Windows build:

```powershell
.\dist\SysScope.exe
```

The Windows application can use the native host or a discovered WSL
distribution as its metrics source. No SysScope GUI runs inside WSL.

### Linux

Python 3.12+, a graphical X11 or Wayland session, and the NVIDIA driver/NVML
are required for GPU monitoring.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m sysscope
```

To run a packaged Linux build:

```bash
chmod +x dist/SysScope
./dist/SysScope
```

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

