# FLIMPA masking manual

This document describes manual and automatic masking in FLIMPA (Python source builds with masking enabled). It covers the **Instruments** menu, every auto-segmentation parameter, how masks are applied to analysis, and how to save or import mask files.

For the original FLIMPA workflow (phasor analysis, reference files, etc.), see the main [README](../README.md) and the published user manual.

---

## Overview

FLIMPA supports three related ways to restrict which pixels enter phasor / lifetime analysis:

| Method | Where you define it | Saved as | Applied when |
|--------|---------------------|----------|--------------|
| **Manual / auto mask** | Intensity or Lifetime map → **Instruments** | `{name}_mask_polygon.tif` | Immediately in session; on import if file on disk |
| **Phasor ROI mask** | Phasor plot → **ROI** ellipse → **Masking → Save ROI mask** | `{name}_mask_ROI.tif` | After explicit save |
| **Photon threshold** | Parameters panel (min/max photons) | Not saved as mask | Always during `calc_Coordinates` |

Manual and auto masks use the same **labelled uint16 TIFF**: `0` = outside, `1`, `2`, `3`… = separate regions (cells, ROIs, etc.).

---

## Instruments menu

On **Intensity display** and **Lifetime maps**, a small **Instruments ▾** button sits on the top-left of the plot.

1. Click **Instruments ▾** → vertical menu opens over the image.
2. Choose a manual tool (polygon, rectangle, lasso, brush, inspect).
3. The menu closes (use **Back** to leave without choosing).
4. Click **Instruments ▾** again to reopen.

> **Note:** **Auto segment** is temporarily hidden from the Instruments menu (can crash on some data). The implementation remains in `utils/auto_segmentation.py`; set `AUTO_SEGMENT_UI_ENABLED = True` there to restore it.

When **Erase** is active, the button reads **Instruments · Erase ▾**.

### Manual tools

| Tool | Use |
|------|-----|
| **Polygon** | Click vertices; close on first point or **Enter**; **Esc** cancels |
| **Rectangle** | Drag a box |
| **Lasso** | Freehand outline |
| **Brush** | Paint with circular brush; set **Brush size (px)** in the menu (1–30) |
| **Erase** | Toggle: Polygon / Rectangle / Lasso / Brush **remove** mask inside the drawn area |
| **Clear mask** | Remove all regions for the selected file |

**Brush (FLIMfit-style):**

- A new stroke on empty background creates a **new region label**.
- If you **start on an existing region**, you **extend that label** (same as FLIMfit paint).
- Mask updates when you **release** the mouse button.

**Erase (edit / delete parts):**

- Turn on **Erase**, then use **Polygon**, **Rectangle**, **Lasso**, or **Brush**.
- Pixels inside the drawn area are set to `0` (removed from the mask).
- Other region labels are unchanged; region count is updated after each edit.

---

## Auto-segmentation

> **Currently disabled in the UI.** The following documents the feature for when `AUTO_SEGMENT_UI_ENABLED` is turned back on in `utils/auto_segmentation.py`.

**Instruments → Auto segment** runs an algorithm on the **integrated intensity image** (sum over time channels) of the **selected file**, then replaces the current mask. You can refine the result with **Brush** and **Erase**.

Algorithms are ported from FLIMfit’s intensity-based segmentation (`otsu_oht_segmentation.m`, `nth_segmentation.m`).

### Pipeline (both algorithms)

1. Pre-process intensity (algorithm-specific).
2. Threshold to binary foreground.
3. **Morphological smoothing**: erode then dilate with a disk of radius `smoothing` (removes speckle, closes small gaps).
4. **Connected-component labelling** (8-neighbour).
5. **Filter** regions with area &lt; `min_size` pixels².
6. Re-label surviving regions as `1`, `2`, `3`, …

If nothing passes the filters, FLIMPA shows: *“No regions were found…”*

---

### Algorithm 1: Otsu + top-hat

**Best for:** relatively uniform background with bright objects; similar to FLIMfit “Otsu + OHT”.

**Steps:**

1. **White top-hat** and **black top-hat** with disk radius ≈ `scale` pixels enhance bright spots and suppress slow background variations.
2. Combined image: `J = intensity + white_tophat − black_tophat`, normalised to 0–1.
3. **Otsu threshold** on `J` → automatic split between foreground/background histograms.
4. Applied cutoff: `threshold = otsu_level / sensitivity` (capped at 1).

#### Parameters

| Parameter | Default | Meaning |
|-----------|---------|---------|
| **scale** | 100 | Approximate **object width in pixels**. Sets the morphological disk for top-hat / bothat. Use ~the typical diameter of a cell in your image. Too small → noisy; too large → misses detail. |
| **sensitivity** | 1.0 | Divides the Otsu level. **Higher → lower threshold → more pixels included** (expands mask). Try 0.8–2.0 if the mask is too tight or too loose. |
| **smoothing** | 5 | Disk radius (px) for erode+dilate after binarisation. Reduces salt-and-pepper noise. Increase if the mask is fragmented. |
| **min_size** | 200 | Minimum connected region area (px²). Smaller blobs are discarded. Increase to ignore debris; decrease to keep small cells. |

---

### Algorithm 2: Nonlinear top-hat (nth)

**Best for:** uneven background, dim structures; FLIMfit’s local-threshold “nth” method.

**Steps:**

1. **Nonlinear top-hat**: `image × box_avg(image, scale) / box_avg(image, scale × rel_bg_scale)²` (FLIMfit `nonlinear_tophat.m`).
2. Subtract 1, normalise by global max (capped at 10000).
3. Pixels with normalised response ≥ **threshold** (after internal scaling) → foreground.
4. Same smoothing, labelling, and **min_size** filter as Otsu.

#### Parameters

| Parameter | Default | Meaning |
|-----------|---------|---------|
| **scale** | 100 | **Object width (px)** for the inner box average (local mean window ≈ this size). |
| **rel_bg_scale** | 2.0 | Ratio of **background window / object window**. Must be ≥ 1. Larger → broader background estimate (more aggressive background suppression). FLIMfit default: 2. |
| **threshold** | 0.1 | Cut-off on the **normalised** nth image (0–1). **Lower → more foreground**. If nothing is detected, try 0.05; if too much background, try 0.2–0.3. |
| **smoothing** | 5 | Same as Otsu algorithm. |
| **min_size** | 200 | Same as Otsu algorithm. |

---

### Tuning tips

| Problem | Try |
|---------|-----|
| No regions found | Lower **threshold** (nth) or raise **sensitivity** (Otsu); lower **min_size**; smaller **scale** |
| Mask covers whole field | Raise **threshold** / lower **sensitivity**; raise **min_size** |
| Jagged or holey regions | Increase **smoothing** slightly |
| Small debris labelled | Increase **min_size** |
| Large cells split into many labels | Increase **smoothing** or merge manually with brush (paint over with same label) |

---

## How masks affect analysis

When a mask is active for a file:

```text
masked_data = raw_data where mask > 0, else 0
```

`lifetime_parameters()` uses `masked_data` instead of raw data if present. Pixels outside the mask do not contribute to phasor coordinates or lifetime maps.

**Phasor ROI** (ellipse on phasor plot) only **dims the lifetime map preview** until you **Masking → Save ROI mask**.

**Photon min/max** thresholds are applied separately inside `calc_Coordinates` and shown as a teal overlay on intensity.

---

## Saving masks

**Masking** menu:

| Action | Output |
|--------|--------|
| **Save manual mask (polygon)...** | User-chosen path; suggested `{stem}_mask_polygon.tif` |
| **Save ROI mask (from phasor)...** | User-chosen path; suggested `{stem}_mask_ROI.tif` |
| **Clear manual mask for selected file** | Clears in memory only (does not delete files on disk) |

Masks are **uint16 TIFF**, one label per region.

---

## Importing masks

**Load data → Import raw data with manual masks**

1. Select **raw FLIM files** (`.sdt`, `.ptu`, `.tif` stacks — not the mask alone).
2. Choose how to provide masks:
   - **Folder** containing mask TIFFs, or
   - **Individual mask file(s)**.
3. FLIMPA pairs by sample name.

Recognised mask filenames for sample `{stem}`:

- `{stem} segmentation.tif` (legacy)
- `{stem}_mask_polygon.tif`
- `{stem}_mask_FLIMFIT.tif` (legacy, still imported)
- `{stem}_mask_ROI.tif`

Custom names work when importing a **single** mask with a **single** raw file, or if the filename starts with `{stem}_`.

---

## Module map (developers)

| File | Role |
|------|------|
| `utils/mask_editor.py` | Drawing tools, brush, auto-segment hook |
| `utils/auto_segmentation.py` | Otsu + nth algorithms |
| `utils/mask_segment_dialog.py` | Auto-segment parameter dialog |
| `utils/mask_instruments.py` | Floating Instruments UI |
| `utils/mask_io.py` | Save/load/apply, filename resolution |
| `utils/mask_viz.py` | Overlay colours and contours |
| `utils/toolbar.py` | Import with masks, save menu |
| `utils/phasor_plot.py` | Phasor ROI → `_mask_ROI.tif` |

---

## Comparison with FLIMfit

| Feature | FLIMfit | FLIMPA |
|---------|---------|--------|
| Paint brush | Yes | Yes |
| Auto Otsu / nth on intensity | Yes | Yes |
| Membrane / extra algorithms | Yes | Not yet |
| Region filtering (roundness, intensity %) | Yes | Not yet |
| Phasor correlation histogram masks | Yes | Ellipse on g–s only |
| Batch copy mask to all files | Yes | Per file |

Workflow in FLIMPA: **Auto segment → Brush / Erase → Save manual mask → Run analysis**.
