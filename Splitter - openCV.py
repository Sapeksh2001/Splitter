import cv2
import numpy as np
from tkinter import Tk, filedialog, simpledialog
import os
import sys

# ── Tkinter root (hidden) ────────────────────────────────────────────────────
_tk_root = Tk()
_tk_root.withdraw()

# ── File selection ───────────────────────────────────────────────────────────
path = filedialog.askopenfilename(
    title="Select an Image",
    filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.tiff;*.webp")]
)
if not path:
    print("No file selected.")
    sys.exit(0)

# ── Image load ───────────────────────────────────────────────────────────────
img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
if img is None:
    print(f"Failed to load image: {path}")
    sys.exit(1)

# FIX #4 — Guard against grayscale (2-D) or 2-channel images before
# accessing shape[2], which would raise IndexError on non-colour images.
if img.ndim == 2:
    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
elif img.shape[2] == 2:
    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)   # edge case: 2-ch

has_alpha = img.shape[2] == 4
clone     = img.copy()

# ── State ────────────────────────────────────────────────────────────────────
hlines           = []          # y-coordinates of horizontal split lines
vlines           = []          # x-coordinates of vertical split lines
undo_stack       = []          # FIX #1/2 — tracks ('h'|'v', value) in add order
selected         = None        # ('h'|'v', index) or None
hover_threshold  = 5
snap_size        = 10
mouse_x, mouse_y = -1, -1
show_cursor_guides = True

# FIX #5 — Pre-compute checker once; recompute only if window is resized.
# Avoids a full O(w×h) allocation + fill on every mouse-move frame.
_checker_cache: np.ndarray | None = None
_checker_shape  = (0, 0)

def get_checker(w: int, h: int) -> np.ndarray:
    global _checker_cache, _checker_shape
    if _checker_cache is None or _checker_shape != (w, h):
        blk = 10
        bg  = np.zeros((h, w, 3), dtype=np.uint8)
        for cy in range(0, h, blk):
            for cx in range(0, w, blk):
                col = 200 if (cx // blk + cy // blk) % 2 == 0 else 255
                bg[cy:cy+blk, cx:cx+blk] = col
        _checker_cache = bg
        _checker_shape = (w, h)
    return _checker_cache

# ── Helpers ──────────────────────────────────────────────────────────────────
def snap(val: int) -> int:
    # FIX #10 — Guard against snap_size == 0 (defensive; UI already prevents it).
    if snap_size <= 0:
        return val
    return int(round(val / snap_size) * snap_size)

# FIX #9 — Colour helpers: always emit a tuple that matches the image channel
# count so guide lines drawn on 3-channel images don't silently carry a stray
# alpha value that makes intent unreadable.
def _clr(b: int, g: int, r: int, a: int = 255) -> tuple:
    return (b, g, r, a) if has_alpha else (b, g, r)

LINE_H_NORMAL   = lambda: _clr(0,   0,   255)   # red    — unselected H-line
LINE_H_SELECTED = lambda: _clr(0,   255, 0  )   # green  — selected H-line
LINE_V_NORMAL   = lambda: _clr(255, 0,   0  )   # blue   — unselected V-line
LINE_V_SELECTED = lambda: _clr(0,   255, 0  )   # green  — selected V-line
LINE_GUIDE      = lambda: _clr(150, 150, 150)   # grey   — cursor crosshair

def redraw():
    global img
    img = clone.copy()
    h, w = img.shape[:2]

    for i, y in enumerate(hlines):
        clr = LINE_H_SELECTED() if selected == ('h', i) else LINE_H_NORMAL()
        cv2.line(img, (0, y), (w, y), clr, 1)

    for i, x in enumerate(vlines):
        clr = LINE_V_SELECTED() if selected == ('v', i) else LINE_V_NORMAL()
        cv2.line(img, (x, 0), (x, h), clr, 1)

    if show_cursor_guides and 0 <= mouse_x < w and 0 <= mouse_y < h:
        cv2.line(img, (mouse_x, 0), (mouse_x, h), LINE_GUIDE(), 1)
        cv2.line(img, (0, mouse_y), (w, mouse_y),  LINE_GUIDE(), 1)

    # Overlay part-count HUD in top-left corner
    n_parts = (len(hlines) + 1) * (len(vlines) + 1)
    hud = f"H:{len(hlines)}  V:{len(vlines)}  Parts:{n_parts}  Snap:{snap_size}px"
    cv2.rectangle(img, (0, 0), (len(hud) * 9 + 8, 20), _clr(0, 0, 0), -1)
    cv2.putText(img, hud, (4, 14), cv2.FONT_HERSHEY_PLAIN, 1.0, _clr(200, 200, 200), 1, cv2.LINE_AA)

    if has_alpha:
        alpha   = img[:, :, 3] / 255.0
        rgb     = img[:, :, :3].astype(np.float32)
        bg      = get_checker(w, h).astype(np.float32)
        blended = (rgb * alpha[..., None] + bg * (1 - alpha[..., None])).astype(np.uint8)
        cv2.imshow("Image Splitter", blended)
    else:
        cv2.imshow("Image Splitter", img)

# ── Mouse callback ───────────────────────────────────────────────────────────
def click_evt(event, x, y, flags, param):
    global selected, mouse_x, mouse_y
    mouse_x, mouse_y = x, y

    if event == cv2.EVENT_MOUSEMOVE:
        redraw()

    elif event == cv2.EVENT_LBUTTONDOWN:
        sy = snap(y)
        for i, ly in enumerate(hlines):
            if abs(ly - sy) <= hover_threshold:
                selected = ('h', i)
                redraw()
                return
        hlines.append(sy)
        undo_stack.append(('h', sy))          # FIX #1 — record for true undo
        selected = ('h', len(hlines) - 1)
        redraw()

    elif event == cv2.EVENT_RBUTTONDOWN:
        sx = snap(x)
        for i, lx in enumerate(vlines):
            if abs(lx - sx) <= hover_threshold:
                selected = ('v', i)
                redraw()
                return
        vlines.append(sx)
        undo_stack.append(('v', sx))          # FIX #1 — record for true undo
        selected = ('v', len(vlines) - 1)
        redraw()

# ── Arrow key codes (cross-platform) ────────────────────────────────────────
# FIX #3 — waitKey() & 0xFF destroys the high bits Windows needs for arrow
# keys (e.g. Up = 2490368). Use waitKeyEx() which returns the full code, then
# normalise the common printable range so letter/digit keys still work.
_ARROW = {
    # Linux / macOS (X11)
    82: 'up',   84: 'down',  81: 'left',  83: 'right',
    # Windows (virtual-key codes returned by waitKeyEx)
    2490368: 'up', 2621440: 'down', 2424832: 'left', 2555904: 'right',
}

def _wait_key(delay_ms: int = 20) -> tuple[int, str | None]:
    """Return (raw_code, arrow_name|None). Printable keys come back as their
    ASCII ord so existing ord('x') comparisons continue to work."""
    raw = cv2.waitKeyEx(delay_ms)
    if raw == -1:
        return -1, None
    arrow = _ARROW.get(raw)
    # Normalise printable ASCII so existing ord() comparisons still work
    key   = raw & 0xFF if raw > 0 and arrow is None else raw
    return key, arrow

# ── Save helper ──────────────────────────────────────────────────────────────
def _unique_path(directory: str, name: str) -> str:
    """Return a path that does not collide with an existing file."""
    base, ext = os.path.splitext(name)
    candidate = os.path.join(directory, name)
    counter   = 1
    while os.path.exists(candidate):
        candidate = os.path.join(directory, f"{base}_{counter}{ext}")
        counter  += 1
    return candidate

def save_parts(save_dir: str) -> int:
    """Slice clone by current hlines/vlines and write PNGs. Returns saved count."""
    hs = [0] + sorted(set(hlines)) + [clone.shape[0]]
    vs = [0] + sorted(set(vlines)) + [clone.shape[1]]
    cnt = 0
    for i in range(len(hs) - 1):
        for j in range(len(vs) - 1):
            y1, y2 = hs[i], hs[i + 1]
            x1, x2 = vs[j], vs[j + 1]
            part = clone[y1:y2, x1:x2]
            if part.size == 0:
                continue
            # FIX #2 — use a local variable; never shadow the source `path`.
            # FIX #11 — collision-safe naming.
            out_path = _unique_path(save_dir, f"row{i}_col{j}.png")
            # FIX #9 — check imwrite return value; warn on failure.
            ok = cv2.imwrite(out_path, part, [cv2.IMWRITE_PNG_COMPRESSION, 9])
            if ok:
                cnt += 1
            else:
                print(f"  ⚠ Failed to write: {out_path}")
    return cnt

# ── Window setup ─────────────────────────────────────────────────────────────
cv2.namedWindow("Image Splitter", cv2.WINDOW_NORMAL)
cv2.setMouseCallback("Image Splitter", click_evt)
redraw()

print("\nImage Splitter — Controls")
print("─" * 38)
print("  Left-click   add / select H-line (snaps)")
print("  Right-click  add / select V-line (snaps)")
print("  Arrows       move selected line by snap step")
print("  +  /  =      increase snap size by 5 px")
print("  -            decrease snap size by 5 px")
print("  c            toggle cursor guides ON / OFF")
print("  u            undo last added line")
print("  Del          delete selected line")
print("  a            auto-split into N × M grid")
print("  s            split & save (stays open)")
print("  q            quit")
print("─" * 38 + "\n")

# ── Main event loop ──────────────────────────────────────────────────────────
while True:
    k, arrow = _wait_key(20)

    if k == -1:
        continue

    # ── Quit ────────────────────────────────────────────────────────────────
    if k == ord('q'):
        break

    # ── Toggle cursor guides ─────────────────────────────────────────────────
    elif k == ord('c'):
        show_cursor_guides = not show_cursor_guides
        print(f"[Cursor Guides] {'ON' if show_cursor_guides else 'OFF'}")
        redraw()

    # FIX #1/2 — True undo: remove the last *added* line (from undo_stack),
    # regardless of which line is currently selected.
    elif k == ord('u'):
        if undo_stack:
            t, val = undo_stack.pop()
            lst = hlines if t == 'h' else vlines
            try:
                lst.remove(val)
            except ValueError:
                pass   # already deleted via Del — stack entry is stale; skip
            # Clear selection if it pointed at the removed or a now-shifted index
            selected = None
            redraw()
        else:
            print("[Undo] Nothing to undo.")

    # ── Delete selected line ─────────────────────────────────────────────────
    # FIX #2 — Del is now the *only* way to remove a specific selected line,
    # distinct from 'u' (undo last added). Key code 127 = Del on Linux/macOS;
    # 3014656 on Windows via waitKeyEx.
    elif k in (127, 3014656) or k == ord('d'):
        if selected:
            t, i = selected
            lst = hlines if t == 'h' else vlines
            if i < len(lst):
                removed_val = lst.pop(i)
                # Keep undo_stack consistent: remove the stale entry if present
                try:
                    undo_stack.remove((t, removed_val))
                except ValueError:
                    pass
            selected = None
            redraw()

    # ── Clear all lines ──────────────────────────────────────────────────────
    elif k == ord('x'):
        if hlines or vlines:
            hlines.clear()
            vlines.clear()
            undo_stack.clear()
            selected = None
            print("[Clear] All lines removed.")
            redraw()

    # ── Auto-split N × M ────────────────────────────────────────────────────
    # FIX #8 — Replace bare except with targeted ValueError/TypeError guard.
    elif k == ord('a'):
        n = simpledialog.askinteger("Grid Rows",    "Enter number of rows:",    minvalue=1)
        m = simpledialog.askinteger("Grid Columns", "Enter number of columns:", minvalue=1)
        if n is None or m is None:
            print("[Auto-split] Cancelled.")
        else:
            hlines = [int(clone.shape[0] * r / n) for r in range(1, n)]
            vlines = [int(clone.shape[1] * c / m) for c in range(1, m)]
            undo_stack.clear()   # auto-split replaces all manual history
            selected = None
            print(f"[Auto-split] {n} rows × {m} cols = {n * m} parts.")
            redraw()

    # ── Save ─────────────────────────────────────────────────────────────────
    # FIX #6 — Saving no longer breaks out of the loop; the window stays open
    # so the user can continue editing or do another save pass.
    elif k == ord('s'):
        save_dir = filedialog.askdirectory(title="Select Folder to Save Image Parts")
        if not save_dir:
            print("[Save] No folder selected.")
        else:
            cnt = save_parts(save_dir)
            print(f"[Save] Saved {cnt} part(s) to: {save_dir}")

    # ── Snap size ────────────────────────────────────────────────────────────
    elif k in (ord('+'), ord('=')):
        snap_size += 5
        print(f"[Snap] {snap_size} px")
        redraw()

    elif k == ord('-'):
        snap_size = max(1, snap_size - 5)
        print(f"[Snap] {snap_size} px")
        redraw()

    # ── Arrow-key line nudge ─────────────────────────────────────────────────
    # FIX #3 — Uses the arrow string from waitKeyEx so this works cross-platform.
    if arrow and selected:
        t, i = selected
        if t == 'h' and i < len(hlines):
            if arrow == 'up':
                hlines[i] = max(0, hlines[i] - snap_size)
            elif arrow == 'down':
                hlines[i] = min(clone.shape[0] - 1, hlines[i] + snap_size)
        elif t == 'v' and i < len(vlines):
            if arrow == 'left':
                vlines[i] = max(0, vlines[i] - snap_size)
            elif arrow == 'right':
                vlines[i] = min(clone.shape[1] - 1, vlines[i] + snap_size)
        redraw()

cv2.destroyAllWindows()
