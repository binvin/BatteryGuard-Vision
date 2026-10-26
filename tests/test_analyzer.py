import cv2
import numpy as np
from analyzer import analyze_image


def encode(img):
    ok, buf = cv2.imencode('.png', img)
    assert ok
    return buf.tobytes()


def test_blank_image_flags_evidence():
    img = np.zeros((400, 500, 3), dtype=np.uint8)
    result, marked = analyze_image(encode(img))
    assert result['status'] == 'INSUFFICIENT_EVIDENCE'
    assert marked


def test_invalid_image_rejected():
    try:
        analyze_image(b'hello')
    except ValueError:
        pass
    else:
        raise AssertionError('invalid image should be rejected')


def test_dark_line_cue_is_detected():
    # A synthetic dark mark is a detection test, not evidence of battery accuracy.
    img = np.full((480, 600, 3), 180, dtype=np.uint8)
    cv2.line(img, (90, 200), (260, 208), (35, 35, 35), 4)
    result, _ = analyze_image(encode(img))
    assert result['surface_line_candidates'], result


def test_granular_pale_patch_candidate():
    # Synthetic white scattered grains on gray. Algorithm regression test only.
    rng = np.random.default_rng(7)
    img = np.full((450, 650, 3), 85, dtype=np.uint8)
    for cx,cy in zip(rng.integers(180,380,1100),rng.integers(150,270,1100)):
        cv2.circle(img, (int(cx),int(cy)), 1, (220,220,220), -1)
    report, _ = analyze_image(encode(img))
    assert report['residue_candidates'], report
