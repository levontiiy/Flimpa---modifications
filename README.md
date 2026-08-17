<div align="center">
  <img src="https://github.com/user-attachments/assets/73dee1af-b5dc-4211-b0ce-ba623fe0bdad" alt="icon_filimpa" width="70%">
</div>

# FLIMPA

**FLIMPA** is an open-source app for phasor-plot analysis of raw Time-Correlated Single Photon Counting (TCSPC) Fluorescence Lifetime Imaging Microscopy (FLIM) data.

This repository is a modified build of [FLIMPA v1.4.2](https://github.com/SofiaKapsiani/FLIMPA/releases/tag/v1.4.2). It adds masking, FRET maps, baseline-check decay curves, and related UI. Run it from source (not from the original Windows `.exe`, which does not include these extras).

> **FLIMPA: A Versatile Software for Fluorescence Lifetime Imaging Microscopy Phasor Analysis**, published in *Analytical Chemistry*  
> Sofia Kapsiani, Nino F Läubli, Edward N. Ward, Mona Shehata, Clemens F. Kaminski, Gabriele S. Kaminski Schierle  
> [Molecular Neuroscience Group](https://www.ceb-mng.org/) and [Laser Analytics Group](https://laser.ceb.cam.ac.uk/) (University of Cambridge)

[[FLIMPA (1.4)](https://github.com/SofiaKapsiani/FLIMPA/releases/tag/v1.4.2)] [[paper](https://pubs.acs.org/doi/10.1021/acs.analchem.5c00495)] [[user manual (PowerPoint)](https://docs.google.com/presentation/d/1rq5PuOyjQz3sg_ERyIjXMgyj1betNweTIrD1v64-u7o/edit?usp=sharing)] [[user manual (PDF)](https://pubs.acs.org/doi/suppl/10.1021/acs.analchem.5c00495/suppl_file/ac5c00495_si_002.pdf)] [[citation](#citation)]

## Features

<div align="center">
  <img src="https://github.com/user-attachments/assets/48a6a9b8-3d79-4cb2-a910-56432db24f60" alt="flimpa_abstract_figure" width="80%">
</div>

- Phasor plot generation and analysis
- Fluorescence lifetime and intensity map visualisation
- ROI selection on the phasor plot
- Gallery plots of fluorescence lifetime and intensity maps
- Violin plot analysis
- Table of mean fluorescence lifetime values per image
- Manual masking (polygon, rectangle, lasso, brush) and mask import/export
- FRET efficiency maps (`E = 1 − τ / τ_D`)
- Baseline check: click a pixel to inspect the decay curve
- Lifetime colormap presets and custom colormap loading

---

# Installation

Needs **Python 3.11 or newer**, **pip**, and internet once (to download packages). Works on macOS, Windows, and Linux. You can run it from a terminal or from an IDE (PyCharm, VS Code, Cursor).

There is no separate installer for this fork. The original Windows `.exe` (without these extra features) is still at [FLIMPA v1.4.2](https://github.com/SofiaKapsiani/FLIMPA/releases/tag/v1.4.2).

## 1. Download the code

```bash
git clone https://github.com/levontiiy/Flimpa---modifications.git
cd Flimpa---modifications
```

Or download the ZIP from GitHub and open that folder.

## 2. Create a virtual environment

**conda**

```bash
conda create --name flimpa_env python=3.11 -y
conda activate flimpa_env
```

**or venv**

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate          # macOS / Linux
```

```bat
.venv\Scripts\activate             # Windows
```

## 3. Install packages

```bash
pip install -r requirements.txt
```

Optional developer extras (pytest):

```bash
pip install -r requirements-dev.txt
```

## 4. Run

```bash
python main.py
```

On some systems use `python3 main.py`.

### PyCharm

1. Open this folder as a project.
2. Settings → Python Interpreter → add a virtualenv (or use the conda env).
3. Install from `requirements.txt` (or accept PyCharm’s prompt to install).
4. Right-click `main.py` → Run.

### VS Code / Cursor

1. Open this folder.
2. Select the interpreter from `.venv` or `flimpa_env`.
3. Run `main.py` from the terminal (with the env activated) or the Run button.

## Checks

If `python main.py` fails with `ModuleNotFoundError`, the virtual environment is not active, or packages were installed for a different Python. Activate the env and run `pip install -r requirements.txt` again.

If `git` is not installed, download the repository ZIP instead.

---

# Usage

For the original FLIMPA workflow, also see the online manuals ([PowerPoint](https://docs.google.com/presentation/d/1rq5PuOyjQz3sg_ERyIjXMgyj1betNweTIrD1v64-u7o/edit?usp=sharing) and [PDF](https://pubs.acs.org/doi/suppl/10.1021/acs.analchem.5c00495/suppl_file/ac5c00495_si_002.pdf)).

![intro_v1 4](https://github.com/user-attachments/assets/81cd375b-d5af-4eec-931f-b3ca2f0ef38e)

## Importing data

FLIMPA accepts `.sdt`, `.ptu`, and `.tif` files. A **reference file** with a known lifetime (for example Rhodamine 6G or Erythrosin B) is required to correct for instrumental response.

For best results, use spatial sizes up to 512 × 512. Files larger than about 1000 × 1000 can be analysed but may be slow or run out of memory.

> **Importing `.tif` files**  
> Data must be `(time, x, y)`. You will be asked for the **bin width** (ns).  
> If it is unknown, **Estimate** uses `(1 / (laser frequency in Hz × number of bins)) × 10^9`. That estimate can be wrong depending on acquisition settings.

For `.ptu` files, see slides 5–6 of the [online user manual](https://docs.google.com/presentation/d/1rq5PuOyjQz3sg_ERyIjXMgyj1betNweTIrD1v64-u7o/edit?usp=sharing).

Sample `.sdt` files are in `sample_data/` (COS-7 cells, SiR-tubulin, Nocodazole-treated and controls from the publication).

Import options (menu **Load data**):

- Import raw data
- Import raw data and assign experimental conditions (e.g. treated vs untreated)
- Import raw data with manually created masks (draw in FLIMPA or import mask TIFFs — see [Masking](#masking))

*Example: importing raw data and assigning experimental conditions*

![condition_assignment_v1 4](https://github.com/user-attachments/assets/b7576e13-c74f-40dd-b6f4-d93d88231342)

FLIMPA currently accepts single files, not time-lapse series.

## Running phasor plot analysis

Set these parameters, then click **Run Phasor Plot Analysis**:

- `Laser Frequency` (MHz)
- Upload a `Reference File`
- `Reference File Lifetime` (ns)
- `Pixel block size` (default 3×3) — spatial averaging of neighbouring pixels before phasor calculation (not the decay time axis)
- `Minimum Photon Count Threshold` (optional; at least 100 photons per pixel is recommended)
- `Maximum Photon Count Threshold` (optional)
- `Baseline correction` (`True` removes constant DC noise from the decay, which helps the Fourier transform)
- `% time channels (baseline corr.)` (default 3.5%) — fraction of the **earliest delay-time channels** used for baseline correction, not spatial pixel grouping

**Warning:** if real fluorescence is already present in the earliest time channels (for example after heavy `.ptu` time binning), baseline correction will subtract signal as well as noise. See slide 11 of the [online user manual](https://docs.google.com/presentation/d/1rq5PuOyjQz3sg_ERyIjXMgyj1betNweTIrD1v64-u7o/edit?usp=sharing).

*Example: importing a reference file, setting a photon threshold, and running analysis*

![reference_upload_v1 4](https://github.com/user-attachments/assets/205d32d9-488d-4cbb-94b9-ccad854419be)

## Phasor plot visualisation

You can plot one image or several samples together, as `scatter`, `histogram`, or `contour`.

![plot_options_v1 4](https://github.com/user-attachments/assets/b51e1d2f-f068-4ec5-bab9-1d6389661ea6)

## Intensity display and colormap

On **Intensity display**, Settings at the bottom of the tab:

- **Colormap** — lifetime / phasor colour scale (Rainbow, Viridis, …, or Custom)
- **Load custom...** — CSV/TXT (R,G,B rows) or a horizontal colour-strip image

Image navigation on intensity / lifetime / FRET plots: pan, reset, zoom in, zoom out (top-right of the image). **Masking ▾** is top-left.

## Lifetime maps and baseline check

After analysis, **Lifetime maps** Settings include min/max lifetime, which map (average / M / phi), integrate intensity, and:

- **Baseline check** — click a pixel on the lifetime image to inspect the decay curve (uses **Pixel block size**)

## FRET

After analysis, the **FRET** tab shows `E = 1 − τ / τ_D`. Set donor lifetime `τ_D` (default 4 ns) and the display range in that tab’s Settings.

## Saving data

**Save** menu:

- **Lifetime and intensity maps** — `.png` and raw `.tif`
- **Gallery visualisations** — lifetime and intensity galleries as `.png`
- **Phasor plots and violin plots** — transparent background
- **Statistical data** — `.csv` of mean fluorescence lifetime per image
- **Manual / ROI masks** — uint16 TIFF via the **Masking** menu (see below)

<img width="1644" height="951" alt="save_data-42" src="https://github.com/user-attachments/assets/17e8f17e-5780-4461-9d7c-c76dc6100ff9" />

---

# Masking

Three ways to restrict which pixels enter phasor / lifetime analysis:

| Method | Where you define it | Saved as | Applied when |
|--------|---------------------|----------|--------------|
| **Manual mask** | Intensity or Lifetime map → **Masking ▾** | `{name}_mask_polygon.tif` | Immediately in the session; on import if the file is on disk |
| **Phasor ROI mask** | Phasor plot → **ROI** ellipse → **Masking → Save ROI mask** | `{name}_mask_ROI.tif` | After you save |
| **Photon threshold** | Parameters panel (min/max photons) | Not saved as a mask | Always during analysis |

Manual masks are **labelled uint16 TIFF**: `0` = outside, `1`, `2`, `3`… = separate regions.

When a mask is active:

```text
masked_data = raw_data where mask > 0, else 0
```

Pixels outside the mask do not contribute to phasor coordinates or lifetime maps.

**Phasor ROI** (ellipse) only dims the lifetime-map preview until you use **Masking → Save ROI mask**.

Photon min/max thresholds are applied separately and shown as a teal overlay on intensity.

## Drawing tools

On **Intensity display** and **Lifetime maps**, **Masking ▾** is at the top-left of the image.

1. Click **Masking ▾**.
2. Choose a tool (polygon, rectangle, lasso, brush).
3. The menu closes (**Back** leaves without choosing a tool).
4. Click **Masking ▾** again to reopen.

When **Erase** is on, the button reads **Masking · Erase ▾**.

| Tool | Use |
|------|-----|
| **Polygon** | Click vertices; close on the first point or **Enter**; **Esc** cancels |
| **Rectangle** | Drag a box |
| **Lasso** | Freehand outline |
| **Brush** | Paint with a circular brush; set **Brush size (px)** in the menu (1–30) |
| **Erase** | Toggle: Polygon / Rectangle / Lasso / Brush **remove** mask inside the drawn area |
| **Clear mask** | Remove all regions for the selected file |

**Brush:** a stroke on empty background creates a **new** region label. Starting on an existing region **extends that label**. The mask updates when you release the mouse.

**Erase:** turn on **Erase**, then draw. Pixels inside the area are set to `0`. Other labels stay; the region count updates after each edit.

Typical workflow: **draw mask → save → Run Phasor Plot Analysis**.

## Saving and clearing masks

**Masking** menu (top menu bar):

| Action | Output |
|--------|--------|
| **Save manual mask (polygon)...** | Suggested `{stem}_mask_polygon.tif` |
| **Save ROI mask (from phasor)...** | Suggested `{stem}_mask_ROI.tif` |
| **Clear manual mask for selected file** | Clears in memory only (does not delete files on disk) |

## Importing masks

**Load data → Import raw data with manual masks** (or the “by condition” variant):

1. Select **raw FLIM files** (`.sdt`, `.ptu`, `.tif` stacks — not the mask alone).
2. Choose a **folder** of mask TIFFs, or **individual mask file(s)**.
3. FLIMPA pairs masks to samples by name.

Recognised names for sample `{stem}`:

- `{stem}_segmentation.tif`
- `{stem}_mask_polygon.tif`
- `{stem}_mask_ROI.tif`
- `{stem} segmentation.tif` (legacy name with a space; still imported)

A custom name works when importing a **single** mask with a **single** raw file, or if the filename starts with `{stem}_`.

## Auto-segmentation (not shown in the UI)

Auto-segmentation is implemented but hidden. To show **Masking → Auto segment**, set `AUTO_SEGMENT_UI_ENABLED = True` in `utils/auto_segmentation.py`.

It runs on the **integrated intensity image** (sum over time) of the selected file, then replaces the current mask. You can refine with **Brush** and **Erase**.

Algorithms: **Otsu + top-hat** and **nonlinear top-hat (nth)**.

Shared pipeline:

1. Pre-process intensity (algorithm-specific).
2. Threshold to binary foreground.
3. Morphological smoothing: erode then dilate with a disk of radius `smoothing`.
4. Connected-component labelling (8-neighbour).
5. Drop regions smaller than `min_size` pixels².
6. Re-label survivors as `1`, `2`, `3`, …

### Otsu + top-hat

Best for a relatively uniform background with bright objects.

`J = intensity + white_tophat − black_tophat`, then Otsu on `J`. Cutoff: `threshold = otsu_level / sensitivity`.

| Parameter | Default | Meaning |
|-----------|---------|---------|
| **scale** | 100 | Approximate object width in pixels (typical cell diameter). Too small → noisy; too large → misses detail. |
| **sensitivity** | 1.0 | Divides the Otsu level. Higher → more pixels included. Try 0.8–2.0. |
| **smoothing** | 5 | Disk radius (px) after binarisation. Increase if the mask is fragmented. |
| **min_size** | 200 | Minimum region area (px²). Increase to ignore debris. |

### Nonlinear top-hat (nth)

Best for uneven background or dim structures.

| Parameter | Default | Meaning |
|-----------|---------|---------|
| **scale** | 100 | Object width (px) for the inner local-mean window. |
| **rel_bg_scale** | 2.0 | Background window / object window (≥ 1). Larger → stronger background suppression. |
| **threshold** | 0.1 | Cut-off on the normalised nth image (0–1). Lower → more foreground. |
| **smoothing** | 5 | Same as Otsu. |
| **min_size** | 200 | Same as Otsu. |

Tuning:

| Problem | Try |
|---------|-----|
| No regions found | Lower **threshold** (nth) or raise **sensitivity** (Otsu); lower **min_size**; smaller **scale** |
| Mask covers the whole field | Raise **threshold** / lower **sensitivity**; raise **min_size** |
| Jagged or holey regions | Increase **smoothing** |
| Small debris labelled | Increase **min_size** |
| Large cells split into many labels | Increase **smoothing**, or merge with the brush (same label) |

---

# Citation

If FLIMPA was useful, please cite:

```
@article{kapsiani2025flimpa,
  title={FLIMPA: A versatile software for Fluorescence Lifetime Imaging Microscopy Phasor Analysis},
  author={Kapsiani, Sofia and Läubli, Nino F and Ward, Edward N and Shehata, Mona and Kaminski, Clemens F and Kaminski Schierle, Gabriele S},
  journal={Analytical Chemistry},
  year={2025},
  publisher={ACS Publications}
}
```
