# Image Splitter — OpenCV

An interactive desktop tool for slicing images into a grid of parts using
manually placed or auto-generated split lines. Supports PNG transparency,
live checker-board preview, cross-platform arrow-key control, and non-destructive
undo.

---

## Features

- **Left-click** to place horizontal split lines; **right-click** for vertical
- Lines snap to a configurable pixel grid
- Selected lines are highlighted in green; nudge them with arrow keys
- Live grey crosshair shows exact cursor position
- Transparent PNG images are previewed over a checker-board background
- On-canvas HUD shows current line counts, part count, and snap size
- Auto-split into an exact N × M grid
- True per-line **undo** (most-recently-added) separate from **delete selected**
- Clear all lines with a single key
- Save exports each slice as an individual PNG with collision-safe naming
- Window **stays open** after saving so you can continue editing

---

## Requirements

- Python 3.10 or later (uses `X | Y` union type hints)
- See `requirements.txt` for packages

---

## Installation

```bash
pip install -r requirements.txt
```

> **Linux users:** Tkinter is not always bundled with the system Python.
> Install it with your package manager if the file dialog fails to open:
> ```bash
> # Debian / Ubuntu
> sudo apt install python3-tk
> # Fedora
> sudo dnf install python3-tkinter
> ```

---

## Usage

```bash
python "Splitter_-_openCV.py"
```

A file-picker dialog opens immediately. Select any PNG, JPEG, BMP, TIFF, or
WebP image. The splitter window then opens.

### Controls

| Input | Action |
|---|---|
| Left-click | Add / select a horizontal line |
| Right-click | Add / select a vertical line |
| Arrow keys | Move the selected line by one snap step |
| `+` / `=` | Increase snap size by 5 px |
| `-` | Decrease snap size by 5 px |
| `c` | Toggle cursor guide-lines ON / OFF |
| `u` | Undo the last *added* line |
| `Del` or `d` | Delete the currently *selected* line |
| `x` | Clear **all** lines |
| `a` | Auto-split into N × M grid |
| `s` | Save all slices to a chosen folder |
| `q` | Quit |

### Saving

Press `s`, pick an output folder, and every slice is saved as
`row{R}_col{C}.png`. If a file with that name already exists it is given a
numeric suffix (`row0_col0_1.png`, etc.) rather than overwritten. A warning is
printed for any slice that could not be written (permissions, full disk, etc.).

---

## Known Platform Notes

| Platform | Notes |
|---|---|
| Windows | Arrow keys work via `waitKeyEx`; `Del` key code `3014656` is handled |
| macOS | Tested on X11-backed OpenCV builds; native Metal builds may vary |
| Linux | All features tested on X11 |

---

## Bug Fixes Applied (vs original)

| # | Severity | Fix |
|---|---|---|
| 1 | 🔴 Bug | `u` now undoes the **last added** line via an undo stack, not the selected line |
| 2 | 🔴 Bug | `Del` / `d` is the dedicated **delete selected** key; the two actions are distinct |
| 3 | 🔴 Bug | Arrow keys work on **Windows** via `cv2.waitKeyEx()` instead of `waitKey() & 0xFF` |
| 4 | 🔴 Bug | Grayscale and 2-channel images are up-converted to BGR instead of crashing on `shape[2]` |
| 5 | 🟠 Perf | Checker-board background is **cached** and only recomputed on dimension change |
| 6 | 🟠 UX | Saving no longer closes the app; window stays open for further editing |
| 7 | 🟠 UX | Added **Clear all** (`x`) shortcut |
| 8 | 🟡 Style | Bare `except: pass` replaced with targeted `None`-check on dialog result |
| 9 | 🟡 Style | Line colours always match the image channel count (3-ch vs 4-ch BGRA tuples) |
| 10 | 🟡 Robust | `imwrite` return value is checked; failures print a warning instead of silent loss |
| 11 | 🟡 Robust | Output filenames are **collision-safe** (numeric suffix if file already exists) |
| 12 | 🟡 Robust | `snap()` guards against division by zero |
| 13 | 🟡 UX | On-canvas HUD shows live H/V counts, total parts, and snap size |

---

## License

MIT — use freely, attribution appreciated.
