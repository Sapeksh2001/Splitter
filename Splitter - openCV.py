import cv2
import numpy as np
from tkinter import Tk, filedialog, simpledialog
import os

Tk().withdraw()
path = filedialog.askopenfilename(title="Select an Image", filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
if not path:
    print("No file selected.")
    exit()

img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
if img is None:
    print("Failed to load image.")
    exit()

clone = img.copy()
hlines = []
vlines = []
selected = None
hover_threshold = 5
snap_size = 10
has_alpha = True if img.shape[2] == 4 else False
mouse_x, mouse_y = -1, -1
show_cursor_guides = True

def MakeChecker(w, h):
    blk = 10
    bg = np.zeros((h, w, 3), dtype=np.uint8)
    for y in range(0, h, blk):
        for x in range(0, w, blk):
            color = 200 if (x // blk + y // blk) % 2 == 0 else 255
            bg[y:y+blk, x:x+blk] = color
    return bg

def Snap(val):
    return int(round(val / snap_size) * snap_size)

def Redraw():
    global img
    img = clone.copy()

    for i, y in enumerate(hlines):
        clr = (0, 255, 0, 255) if selected == ('h', i) else (0, 0, 255, 255)
        cv2.line(img, (0, y), (img.shape[1], y), clr, 1)
    for i, x in enumerate(vlines):
        clr = (0, 255, 0, 255) if selected == ('v', i) else (255, 0, 0, 255)
        cv2.line(img, (x, 0), (x, img.shape[0]), clr, 1)

    if show_cursor_guides and 0 <= mouse_x < img.shape[1] and 0 <= mouse_y < img.shape[0]:
        cv2.line(img, (mouse_x, 0), (mouse_x, img.shape[0]), (150, 150, 150, 255), 1)
        cv2.line(img, (0, mouse_y), (img.shape[1], mouse_y), (150, 150, 150, 255), 1)

    if has_alpha:
        alpha = img[:, :, 3] / 255.0
        rgb = img[:, :, :3].astype(np.float32)
        bg = MakeChecker(img.shape[1], img.shape[0]).astype(np.float32)
        blended = (rgb * alpha[..., None] + bg * (1 - alpha[..., None])).astype(np.uint8)
        cv2.imshow("Image Splitter", blended)
    else:
        cv2.imshow("Image Splitter", img)

def ClickEvt(event, x, y, flags, param):
    global selected, mouse_x, mouse_y
    mouse_x, mouse_y = x, y
    if event == cv2.EVENT_MOUSEMOVE:
        Redraw()
    elif event == cv2.EVENT_LBUTTONDOWN:
        y = Snap(y)
        for i, ly in enumerate(hlines):
            if abs(ly - y) <= hover_threshold:
                selected = ('h', i)
                Redraw()
                return
        hlines.append(y)
        selected = ('h', len(hlines) - 1)
        Redraw()
    elif event == cv2.EVENT_RBUTTONDOWN:
        x = Snap(x)
        for i, lx in enumerate(vlines):
            if abs(lx - x) <= hover_threshold:
                selected = ('v', i)
                Redraw()
                return
        vlines.append(x)
        selected = ('v', len(vlines) - 1)
        Redraw()

cv2.namedWindow("Image Splitter", cv2.WINDOW_NORMAL)
cv2.setMouseCallback("Image Splitter", ClickEvt)
Redraw()

print("\nInstructions:")
print("• Left-click: add/select horizontal line (snaps to grid)")
print("• Right-click: add/select vertical line (snaps to grid)")
print("• Arrows: move selected line")
print("• '+' / '-' to adjust snap size")
print("• 'c' = toggle cursor guides ON/OFF")
print("• 'u' = undo last line")
print("• 'Del' = delete selected line")
print("• 'a' = auto split into N×M")
print("• 's' = split & save")
print("• 'q' = quit\n")

while True:
    k = cv2.waitKey(20) & 0xFF
    if k == ord('q'):
        break

    elif k == ord('c'):
        show_cursor_guides = not show_cursor_guides
        print(f"[Cursor Guide Lines] {'ON' if show_cursor_guides else 'OFF'}")
        Redraw()

    elif k == ord('u'):
        if selected:
            t, i = selected
            if t == 'h' and hlines:
                hlines.pop(i)
            elif t == 'v' and vlines:
                vlines.pop(i)
            selected = None
            Redraw()

    elif k == 127:  # Del key
        if selected:
            t, i = selected
            if t == 'h' and i < len(hlines):
                hlines.pop(i)
            elif t == 'v' and i < len(vlines):
                vlines.pop(i)
            selected = None
            Redraw()

    elif k == ord('a'):
        try:
            n = simpledialog.askinteger("Grid Rows", "Enter number of rows:")
            m = simpledialog.askinteger("Grid Columns", "Enter number of columns:")
            if not n or not m: continue
            hlines = [int(clone.shape[0] * i / n) for i in range(1, n)]
            vlines = [int(clone.shape[1] * j / m) for j in range(1, m)]
            selected = None
            Redraw()
        except:
            pass

    elif k == ord('s'):
        save_dir = filedialog.askdirectory(title="Select Folder to Save Image Parts")
        if not save_dir:
            print("No folder selected.")
            continue

        hs = sorted(set(hlines))
        vs = sorted(set(vlines))
        hs = [0] + hs + [clone.shape[0]]
        vs = [0] + vs + [clone.shape[1]]

        cnt = 0
        for i in range(len(hs) - 1):
            for j in range(len(vs) - 1):
                y1, y2 = hs[i], hs[i + 1]
                x1, x2 = vs[j], vs[j + 1]
                part = clone[y1:y2, x1:x2]
                if part.size > 0:
                    name = f'row{i}_col{j}.png'
                    path = os.path.join(save_dir, name)
                    cv2.imwrite(path, part, [cv2.IMWRITE_PNG_COMPRESSION, 9])
                    cnt += 1
        print(f"Saved {cnt} parts to: {save_dir}")
        break

    elif k == ord('+') or k == ord('='):
        snap_size += 5
        print(f"[+] Snap size: {snap_size}px")

    elif k == ord('-') and snap_size > 1:
        snap_size = max(1, snap_size - 5)
        print(f"[-] Snap size: {snap_size}px")

    elif selected:
        t, i = selected
        if t == 'h':
            if k == 82: hlines[i] = max(0, hlines[i] - snap_size)
            elif k == 84: hlines[i] = min(img.shape[0] - 1, hlines[i] + snap_size)
        elif t == 'v':
            if k == 81: vlines[i] = max(0, vlines[i] - snap_size)
            elif k == 83: vlines[i] = min(img.shape[1] - 1, vlines[i] + snap_size)
        Redraw()

cv2.destroyAllWindows()
