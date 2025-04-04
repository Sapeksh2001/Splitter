# =========================
# 1. OPENCV + DIALOGS STYLE
# =========================

import cv2
import numpy as np
from tkinter import Tk, filedialog, simpledialog
import os

# === Setup ===
Tk().withdraw()
img_paths = filedialog.askopenfilenames(title="Select Images", filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
if not img_paths:
    print("No images selected.")
    exit()

out_dir = filedialog.askdirectory(title="Select Output Folder")
if not out_dir:
    print("No output folder selected.")
    exit()

fmt = simpledialog.askstring("Save Format", "Enter file format (png/jpg):", initialvalue="png")
if fmt not in ('png', 'jpg'):
    fmt = 'png'

# === Start Processing ===
for path in img_paths:
    base_img = cv2.imread(path)
    if base_img is None:
        print(f"Failed to load {path}")
        continue

    # Add padding of 5 pixels
    clone = cv2.copyMakeBorder(base_img, 5, 5, 5, 5, cv2.BORDER_CONSTANT, value=[255, 255, 255])
    orig_h, orig_w = clone.shape[:2]
    hlines, vlines = [], []
    img = clone.copy()
    selected_line = [None]  # wrap in list to allow modification in nested functions

    def redraw():
        global img
        img = clone.copy()
        for i, y in enumerate(hlines):
            color = (0, 255, 0) if selected_line[0] == ('h', i) else (0, 0, 255)
            cv2.line(img, (0, y), (img.shape[1], y), color, 1)
        for i, x in enumerate(vlines):
            color = (0, 255, 0) if selected_line[0] == ('v', i) else (255, 0, 0)
            cv2.line(img, (x, 0), (x, img.shape[0]), color, 1)

        # Fixed aspect ratio
        screen_h, screen_w = 720, 1280
        scale = min(screen_w / orig_w, screen_h / orig_h)
        w = int(orig_w * scale)
        h = int(orig_h * scale)
        resized = cv2.resize(img, (w, h))
        cv2.imshow("Splitter", resized)

    def click_event(event, x, y, flags, param):
        screen_h, screen_w = 720, 1280
        scale = min(screen_w / orig_w, screen_h / orig_h)
        x = int(x / scale)
        y = int(y / scale)

        if event == cv2.EVENT_LBUTTONDOWN:
            for i, ly in enumerate(hlines):
                if abs(ly - y) <= 5:
                    selected_line[0] = ('h', i)
                    redraw()
                    return
            hlines.append(y)
            selected_line[0] = ('h', len(hlines) - 1)
            redraw()
        elif event == cv2.EVENT_RBUTTONDOWN:
            for i, lx in enumerate(vlines):
                if abs(lx - x) <= 5:
                    selected_line[0] = ('v', i)
                    redraw()
                    return
            vlines.append(x)
            selected_line[0] = ('v', len(vlines) - 1)
            redraw()

    cv2.namedWindow("Splitter", cv2.WINDOW_NORMAL)
    cv2.setMouseCallback("Splitter", click_event)
    redraw()

    print(f"\nImage: {os.path.basename(path)}")
    print("Click to add lines. Arrows to move. 'z' to undo. 's' to split. 'q' to skip.")

    while True:
        k = cv2.waitKey(0) & 0xFF
        if k == ord('q'):
            break
        elif k == ord('s'):
            h = sorted(set(hlines))
            v = sorted(set(vlines))
            h = [0] + h + [clone.shape[0]]
            v = [0] + v + [clone.shape[1]]
            regions = []
            for i in range(len(h) - 1):
                for j in range(len(v) - 1):
                    y1, y2 = h[i], h[i + 1]
                    x1, x2 = v[j], v[j + 1]
                    regions.append(clone[y1:y2, x1:x2])
            labels = []
            for i, r in enumerate(regions):
                win = f"Region Preview - {i}"
                cv2.imshow(win, r)
                cv2.waitKey(1)
                lbl = simpledialog.askstring("Label", f"Enter label for region {i} (preview shown):")
                labels.append(lbl if lbl else f"unknown_{i}")
                cv2.destroyWindow(win)
            for i, (r, lbl) in enumerate(zip(regions, labels)):
                save_path = os.path.join(out_dir, f"{lbl}.{fmt}")
                cv2.imwrite(save_path, r)
            break
        elif k == ord('z'):
            if selected_line[0]:
                t, i = selected_line[0]
                if t == 'h' and 0 <= i < len(hlines):
                    hlines.pop(i)
                elif t == 'v' and 0 <= i < len(vlines):
                    vlines.pop(i)
                selected_line[0] = None
                redraw()
        elif selected_line[0]:
            t, i = selected_line[0]
            if t == 'h' and 0 <= i < len(hlines):
                if k == 82: hlines[i] = max(0, hlines[i] - 1)
                elif k == 84: hlines[i] = min(img.shape[0] - 1, hlines[i] + 1)
            elif t == 'v' and 0 <= i < len(vlines):
                if k == 81: vlines[i] = max(0, vlines[i] - 1)
                elif k == 83: vlines[i] = min(img.shape[1] - 1, vlines[i] + 1)
            redraw()

    cv2.destroyAllWindows()

# =========================
# 2. FULL TKINTER GUI (WIP)
# =========================

# If you'd like, I can now build a full GUI version using `tkinter.Canvas` with embedded image, buttons, and line drawing.
# It will support all the above features with an actual UI for undo/save/etc.

# Would you like to proceed with the full GUI build (buttons, canvas, entry boxes)?