<div align="center">
  <img src="https://github.com/user-attachments/assets/73dee1af-b5dc-4211-b0ce-ba623fe0bdad" alt="icon_filimpa" width="70%">
</div>

# FLIMPA

**FLIMPA** is an open-source app for phasor-plot analysis of raw Time-Correlated Single Photon Counting (TCSPC) Fluorescence Lifetime Imaging Microscopy (FLIM) data.

This repository is a modified build of [FLIMPA v1.4.2](https://github.com/SofiaKapsiani/FLIMPA/releases/tag/v1.4.2). It adds in-app masking, FRET maps, baseline-check decay curves, colormaps, and related UI. Run it from source (the original Windows `.exe` does not include these extras).

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
- ROI selection on the phasor plot (ellipse), saved as a mask if you want it in analysis
- Gallery plots of fluorescence lifetime and intensity maps
- Violin plot analysis
- Table of mean fluorescence lifetime values per image
- Manual masking on intensity / lifetime images (polygon, rectangle, lasso, brush) and mask import/export
- FRET efficiency maps (`E = 1 − τ / τ_D`)
- Baseline check: click a pixel on the lifetime map to inspect the decay curve
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

The layout is: parameters and **Run Phasor Plot Analysis** on the left, the phasor plot under that, image tabs in the centre, and the file list on the right. After analysis, extra tabs appear for lifetime maps, galleries, violin plots, and the lifetime table.

Menus: **Load data**, **Reference**, **Masking**, **Save**.

*Video: general features — overview of the app after data are loaded*

![General features](assets/general_features.gif)

## Importing data

FLIMPA accepts `.sdt`, `.ptu`, and `.tif` files. A **reference file** with a known lifetime (for example Rhodamine 6G or Erythrosin B) is required to correct for instrumental response.

For best results, use spatial sizes up to 512 × 512. Files larger than about 1000 × 1000 can be analysed but may be slow or run out of memory.

> **Importing `.tif` files**  
> Data must be `(time, x, y)`. You will be asked for the **bin width** (ns).  
> If it is unknown, **Estimate** uses `(1 / (laser frequency in Hz × number of bins)) × 10^9`. That estimate can be wrong depending on acquisition settings.

For `.ptu` files, see slides 5–6 of the [online user manual](https://docs.google.com/presentation/d/1rq5PuOyjQz3sg_ERyIjXMgyj1betNweTIrD1v64-u7o/edit?usp=sharing).

Sample `.sdt` files are in `sample_data/` (COS-7 cells, SiR-tubulin, Nocodazole-treated and controls from the publication). Example masks are in `sample_data/masks_example/` and `sample_data/Masks_created/`.

**Load data** menu:

- **Import raw data**
- **Import raw data by condition** (e.g. treated vs untreated)
- **Import raw data with manual masks**
- **Import raw data by condition with manual masks**

**Reference** menu:

- **Import reference file** — calibration sample with known lifetime
- **Import IRF** — optional instrument response for the purple overlay in Baseline check

FLIMPA currently accepts single files, not time-lapse series.

*Video: upload files — importing samples (and conditions if you use them)*

![Upload files](assets/upload_files.gif)

## Running phasor plot analysis

Set these parameters (left panel), then click **Run Phasor Plot Analysis**:

| Control | What it does |
|---------|----------------|
| **Frequency (MHz)** | Laser repetition rate |
| **Reference file** | Calibration file imported under **Reference** |
| **Reference lifetime (ns)** | Known lifetime of that reference (also donor `τ_D` for FRET; default 4 ns for Rhodamine 6G) |
| **Pixel block size** | Spatial averaging of neighbouring pixels before phasor calculation (`3×3` default, or `7×7` / `9×9` / `12×12` / `None`). Not the decay time axis |
| **Min. photon counts** / **Max. photon counts** | Pixels outside this intensity range are excluded (teal overlay on **Intensity display**) |
| **Baseline correction** | `True` subtracts a constant offset estimated from the earliest delay channels |
| **% time channels (baseline corr.)** | Fraction of those earliest channels used for the offset (default 3.5%) |

**Warning:** if real fluorescence is already present in the earliest time channels (for example after heavy `.ptu` time binning), baseline correction will subtract signal as well as noise. See slide 11 of the [online user manual](https://docs.google.com/presentation/d/1rq5PuOyjQz3sg_ERyIjXMgyj1betNweTIrD1v64-u7o/edit?usp=sharing).

## Phasor plot

You can show one image or several samples together.

- **τ Labels** — lifetime ticks on the universal circle
- **ROI** — draw an ellipse on the phasor; non-selected pixels are dimmed on the lifetime map (display only until you save the ROI mask)
- **Individual** / **Condition** — one file vs grouped by experimental condition (gallery)
- **Scatter** / **Histogram** / **Contour** — how points are drawn

On **Gallery (tau)**, the **Layers** list (right of the phasor) shows/hides files and sets draw order (▲ / ▼).

## Intensity display

Always available. Settings at the bottom of the tab:

- **Colormap** — lifetime / phasor colour scale (Rainbow, Viridis, Plasma, …, or Custom)
- **Load custom...** — CSV/TXT (R,G,B rows, low → high lifetime) or a horizontal colour-strip image

On intensity, lifetime, and FRET images: **Masking ▾** is top-left; pan / reset / zoom are top-right.

## Lifetime maps

After analysis, **Lifetime maps** Settings:

- **Min. / Max. lifetime (ns)** — colour scale
- **Lifetime map** — `average`, `M` (modulation), or `phi` (phase)
- **Integrate intensity** — grayscale intensity overlay on the colour map
- **Baseline check** — click a pixel to open the decay-curve window (see below)

## Baseline check (decay curve)

1. Open **Lifetime maps**.
2. In that tab’s Settings, turn on **Baseline check**.
3. Click a pixel on the lifetime image.

The **FLIMPA — Baseline check** window shows photon counts vs delay time for that location. It uses **Pixel block size** (the same N×N neighbourhood as analysis).

In the window:

- **Log scale (Y)**
- **Show map τ curve** — purple 1-exp model using τ from the lifetime map
- **Start plot at t₀** — if baseline correction is on, hide the empty pre-t₀ region
- **Use IRF** — purple curve is IRF ⊗ exponential when a reference is loaded; off = plain exponential
- **Move map τ** — slide the purple curve for display only (±5 ns)

*Video: decay curve — Baseline check on a lifetime-map pixel*

![Decay curve](assets/decay_curve.gif)

## FRET

The **FRET** tab shows `E = 1 − τ / τ_D`. Settings:

- **Donor τ_D (ns)** — same value as **Reference lifetime**
- **Lifetime map** — which τ map is used
- **Min. / Max. display range** — colour scale for *E* (default 0–1)

## Gallery, violin plots, and the lifetime table

After analysis:

- **Gallery (tau)** / **Gallery (I)** — one thumbnail per file; lifetime gallery uses the same min/max, map type, and integrate-intensity settings
- **Violin plots** — distribution of lifetimes; choose `average` / `M` / `phi`
- **Lifetime values** — mean lifetime per image; **Group by** None, Condition, or Sample

## Saving data

**Save** menu:

- **Save lifetime maps** — `.png` and raw `.tif`
- **Save lifetime gallery**
- **Save intensity images** / **Save intensity gallery**
- **Save transparent phasor plot** / **Save transparent violin plot**
- **Export lifetime values table** — `.csv`

Masks are saved from the **Masking** menu, not **Save**.

---

# Masking

Three ways to restrict which pixels enter phasor / lifetime analysis:

| Method | Where you define it | Saved as | Applied when |
|--------|---------------------|----------|--------------|
| **Manual mask** | Intensity or Lifetime map → **Masking ▾** | `{name}_mask_polygon.tif` | Immediately in the session; on import if the file is on disk |
| **Phasor ROI mask** | Phasor plot → **ROI** ellipse → **Masking → Save ROI mask** | `{name}_mask_ROI.tif` | After you save |
| **Photon threshold** | Parameters panel (min/max photons) | Not saved as a mask | Always during analysis |

Manual masks are **labelled uint16 TIFF**: `0` = outside, `1`, `2`, `3`… = separate regions.

When a mask is active, pixels with label `0` are set to zero in the analysis cube. They do not contribute to phasor coordinates or lifetime maps.

Photon min/max thresholds are applied separately and shown as a teal overlay on intensity.

## Manual mask (polygon and other drawing tools)

On **Intensity display** and **Lifetime maps**, **Masking ▾** is at the top-left of the image.

1. Click **Masking ▾**.
2. Choose **Polygon**, **Rectangle**, **Lasso**, or **Brush**.
3. Draw on the image. **Back** closes the menu without choosing a tool.
4. **Clear mask** removes all regions for this file **and** stops the drawing tool.

When **Erase** is on, the button reads **Masking · Erase ▾**. Drawing then sets pixels to `0` instead of adding a region.

| Tool | Use |
|------|-----|
| **Polygon** | Click vertices; close on the first point or **Enter**; **Esc** cancels |
| **Rectangle** | Drag a box |
| **Lasso** | Freehand outline |
| **Brush** | Paint with a circular brush; set **Brush size (px)** in the menu (1–30) |
| **Erase** | Toggle: tools **remove** mask inside the drawn area |
| **Clear mask** | Remove all regions and exit masking |

**Brush:** a stroke on empty background creates a **new** region label. Starting on an existing region **extends that label**. The mask updates when you release the mouse.

Typical workflow: **draw mask → Masking → Save manual mask → Run Phasor Plot Analysis**.

*Video: polygon masking — drawing a manual mask on the image*

![Polygon masking](assets/polygon_masking.gif)

## Phasor ROI mask

1. After analysis, click **ROI** above the phasor plot.
2. Drag an ellipse around the phasor cloud you want to keep. The lifetime map dims pixels outside that ellipse (preview only).
3. **Masking → Save ROI mask (from phasor)...** writes `{stem}_mask_ROI.tif` and applies it to analysis.
4. Toggle **ROI** again to clear the ellipse preview.

*Video: ROI masking — ellipse on the phasor plot, then save*

![ROI masking](assets/roi_masking.gif)

## Saving and clearing masks

**Masking** menu (top menu bar):

| Action | Output |
|--------|--------|
| **Save manual mask (polygon)...** | Suggested `{stem}_mask_polygon.tif` |
| **Save ROI mask (from phasor)...** | Suggested `{stem}_mask_ROI.tif` |
| **Clear manual mask for selected file** | Clears in memory only (does not delete files on disk) and exits the drawing tool |

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
