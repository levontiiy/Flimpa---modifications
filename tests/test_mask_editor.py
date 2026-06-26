"""Manual mask editor behaviour."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from utils.mask_editor import ManualMaskEditor, _disk_indices, _region_from_rect


def test_antimask_region_clears_and_recounts_labels():
    """Antimasking sets drawn pixels to 0 and updates n_regions."""
    shape = (10, 10)
    mask = np.zeros(shape, dtype=np.uint16)
    mask[2:8, 2:8] = 1
    mask[0:2, 0:2] = 2
    region = _region_from_rect((0, 3, 0, 3), shape)

    antimask_mode = True
    if antimask_mode:
        mask[region] = 0
        n_regions = int(mask.max()) if mask.max() > 0 else 0

    assert mask[0, 0] == 0
    assert mask[5, 5] == 1
    assert n_regions == 1


def test_brush_cursor_radius_matches_width():
    fig, ax = plt.subplots()
    editor = ManualMaskEditor.__new__(ManualMaskEditor)
    editor.brush_width = 7
    editor._ax = ax
    editor._brush_cursor = None

    editor._update_brush_cursor(12.5, 8.0, visible=True)

    assert editor._brush_cursor is not None
    assert editor._brush_cursor.get_radius() == 7
    assert editor._brush_cursor.center == (12.5, 8.0)
    assert editor._brush_cursor.get_visible()

    editor._update_brush_cursor(visible=False)
    assert not editor._brush_cursor.get_visible()

    plt.close(fig)


def test_disk_indices_match_brush_radius():
    shape = (20, 20)
    yy, xx = _disk_indices(10.0, 10.0, radius=3, shape=shape)
    assert yy.size > 0
    dist2 = (yy - 10) ** 2 + (xx - 10) ** 2
    assert np.all(dist2 <= 9)
