"""BatteryGuard Vision: explainable photo quality and visual anomaly triage.
This is NOT a battery safety assessment or damage diagnosis.
"""
import cv2
import numpy as np

MAX_SIDE = 1200


def analyze_image(image_bytes: bytes):
    if not image_bytes or len(image_bytes) > 10 * 1024 * 1024:
        raise ValueError('Upload a nonempty image smaller than 10 MB.')
    arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError('Could not decode image. Use JPEG or PNG.')
    h0, w0 = img.shape[:2]
    if max(h0, w0) > MAX_SIDE:
        scale = MAX_SIDE / max(h0, w0)
        img = cv2.resize(img, (round(w0*scale), round(h0*scale)), interpolation=cv2.INTER_AREA)
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    brightness = float(np.mean(gray))
    dark_fraction = float(np.mean(gray < 35))
    bright_fraction = float(np.mean(gray > 235))
    flags = []
    if min(h, w) < 320:
        flags.append('Image resolution is low; capture a closer, higher-resolution photo.')
    if blur_score < 70:
        flags.append('Image appears blurry; stabilize the camera and retake.')
    if brightness < 65 or dark_fraction > 0.60:
        flags.append('Image is dark; add diffuse light and retake.')
    if brightness > 215 or bright_fraction > 0.60:
        flags.append('Image is overexposed; reduce glare and retake.')

    # HSV segmentation identifies rust-like orange-brown *colors*, not corrosion.
    # Suppress isolated pixels and extreme border effects. There is NO battery segmentation.
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower = np.array([4, 75, 35], dtype=np.uint8)
    upper = np.array([25, 255, 220], dtype=np.uint8)
    mask = cv2.inRange(hsv, lower, upper)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    min_area = max(120, int(h*w*0.001))
    boxes = []
    for cnt in sorted(contours, key=cv2.contourArea, reverse=True):
        area = cv2.contourArea(cnt)
        if area < min_area or area > h*w*0.35:
            continue
        x, y, bw, bh = cv2.boundingRect(cnt)
        if x <= 2 or y <= 2 or x+bw >= w-2 or y+bh >= h-2:
            continue
        boxes.append({'x': int(x), 'y': int(y), 'width': int(bw), 'height': int(bh), 'area_px': round(float(area))})
        if len(boxes) == 6:
            break
    # Experimental single-image candidate detector: elongated dark surface lines.
    # Black-hat morphology emphasizes thin dark features, e.g., scratches, but can
    # also respond to lettering, seams and shadows. No damage classification.
    line_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (13, 13))
    dark_lines = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, line_kernel)
    _, line_mask = cv2.threshold(dark_lines, 28, 255, cv2.THRESH_BINARY)
    line_mask = cv2.morphologyEx(line_mask, cv2.MORPH_OPEN,
                                cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2)))
    line_contours, _ = cv2.findContours(line_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    line_boxes = []
    for contour in sorted(line_contours, key=cv2.contourArea, reverse=True):
        x, y, bw, bh = cv2.boundingRect(contour)
        aspect = max(bw, bh) / max(1, min(bw, bh))
        if (max(bw, bh) < 28 or aspect < 3.8 or
                cv2.contourArea(contour) < 18 or
                cv2.contourArea(contour) > h*w*0.08):
            continue
        # Exclude regions near image boundaries.
        if x <= 3 or y <= 3 or x+bw >= w-3 or y+bh >= h-3:
            continue
        line_boxes.append({'x': int(x), 'y': int(y), 'width': int(bw),
                           'height': int(bh), 'cue': 'elongated_dark_mark',
                           'interpretation': 'Possible surface mark, seam, print or shadow'})
        if len(line_boxes) >= 8:
            break
    # Experimental white/pale granular deposit cue. This detector is deliberately
    # morphology/texture-based: color-only selection would mark white packaging,
    # paper, labels or glare. It DOES NOT identify electrolyte chemically.
    hsv_channels = cv2.split(hsv)
    saturation, value = hsv_channels[1], hsv_channels[2]
    # Bright, pale pixels, while excluding saturated metal/tape colors.
    pale = ((value >= 145) & (saturation <= 105)).astype(np.uint8)
    # Local texture reveals granular patches instead of smooth painted regions.
    fgray = gray.astype(np.float32)
    local_mean = cv2.GaussianBlur(fgray, (0, 0), 2.2)
    local_sq = cv2.GaussianBlur(fgray*fgray, (0, 0), 2.2)
    local_std = np.sqrt(np.maximum(0, local_sq - local_mean*local_mean))
    granular = ((local_std > 17.0) & (pale > 0)).astype(np.uint8)*255
    # Group nearby flecks without filling a whole white background.
    granular = cv2.morphologyEx(granular, cv2.MORPH_CLOSE,
                 cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (19, 19)))
    num, labels, stats, _ = cv2.connectedComponentsWithStats(granular, 8)
    residue_boxes = []
    for component in sorted(range(1, num), key=lambda k: stats[k, cv2.CC_STAT_AREA], reverse=True):
        x, y, bw, bh, component_area = (int(v) for v in stats[component])
        rect_area = bw*bh
        if rect_area < max(350, h*w*0.002) or rect_area > h*w*0.35:
            continue
        if bw < 20 or bh < 14:
            continue
        area_mask = labels[y:y+bh, x:x+bw] == component
        # A patch needs multiple bright textured flecks, not one text stroke.
        pale_textured_count = int(np.count_nonzero(
            (pale[y:y+bh,x:x+bw] > 0) &
            (local_std[y:y+bh,x:x+bw] > 17) & area_mask))
        if pale_textured_count < 45:
            continue
        residue_boxes.append({'x':x,'y':y,'width':bw,'height':bh,
           'cue':'pale_granular_texture',
           'interpretation':'Possible pale granular residue; could be dust, paint, label, glare or background'})
        if len(residue_boxes) >= 5:
            break
    marked = img.copy()
    for b in boxes:
        cv2.rectangle(marked, (b['x'], b['y']), (b['x']+b['width'], b['y']+b['height']), (0, 165, 255), 3)
    for b in residue_boxes:
        cv2.rectangle(marked, (b['x'],b['y']),
                      (b['x']+b['width'], b['y']+b['height']), (220, 0, 220), 3)
    for b in line_boxes:
        cv2.rectangle(marked, (b['x'], b['y']),
                      (b['x']+b['width'], b['y']+b['height']), (255, 180, 0), 2)
    cv2.putText(marked, 'CANDIDATE VISUAL CUES - NOT DIAGNOSIS', (12, 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.54, (255, 255, 255), 3)
    for b in line_boxes:
        cv2.rectangle(marked, (b['x'], b['y']),
                      (b['x']+b['width'], b['y']+b['height']), (255, 180, 0), 2)
    cv2.putText(marked, 'CANDIDATE VISUAL CUES - NOT DIAGNOSIS', (12, 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.54, (0, 0, 160), 1)
    ok, encoded = cv2.imencode('.jpg', marked, [cv2.IMWRITE_JPEG_QUALITY, 85])
    if not ok:
        raise RuntimeError('Could not encode annotated image.')
    if flags:
        status = 'INSUFFICIENT_EVIDENCE'
        recommendation = 'Retake the battery image with clear focus, diffuse lighting, and the entire casing visible. Do not move or handle a battery that appears hazardous.'
    elif boxes or line_boxes or residue_boxes:
        status = 'VISUAL_REVIEW'
        recommendation = 'Human review recommended for highlighted areas. Orange boxes show color cues; blue boxes show narrow dark marks; magenta boxes show possible pale granular material. Tape, labels, printed text, seams, or shadows may cause false positives. If safe, request a clearer close-up.'
    else:
        status = 'NO_CANDIDATES'
        recommendation = 'No candidate color, pale granular or narrow-line visual cues found. This does not establish battery safety or absence of damage.'
    result = {
        'status': status,
        'quality': {'width': w, 'height': h, 'blur_variance': round(blur_score, 1),
                    'mean_brightness': round(brightness, 1),
                    'dark_fraction': round(dark_fraction, 3), 'bright_fraction': round(bright_fraction, 3),
                    'warnings': flags},
        'regions': boxes,
        'surface_line_candidates': line_boxes,
        'residue_candidates': residue_boxes,
        'detector_notes': 'Magenta: bright granular-texture candidates (dust, leakage-like residue, printed labels or glare). Blue: narrow dark marks (seams/text/shadows). Orange: amber/brown colors (may be tape). None confirms damage.',
        'recommendation': recommendation,
        'limitations': ('Experimental color, granular-residue, line-mark and quality heuristics only; cannot reliably diagnose scratches, swelling, punctures, '
                        'internal damage, thermal risk, or determine whether a battery is safe.'),
        'opencv_version': cv2.__version__,
    }
    return result, encoded.tobytes()
