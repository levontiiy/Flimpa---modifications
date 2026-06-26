"""Movable secondary window for per-pixel decay curves (FLIMfit-style)."""

from __future__ import annotations

import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QMainWindow, QVBoxLayout, QWidget

from utils.decay_inspector import PixelDecay, get_pixel_decay
from utils.decay_fitting import DecayFitResult, fit_single_exponential, predict_decay_at_tau

_TEAL = "#3ca2a1"
_FIT_COLOR = "#FFB347"
_MAP_TAU_COLOR = "#B388FF"
_BG = (18 / 255, 18 / 255, 18 / 255)
_CURSOR_COLOR = "#FFE066"
_ZERO_MARKER_COLOR = "#5a9e9d"


def _aggregate_max_per_time(t: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """One point per delay time; if times repeat, keep the largest count."""
    t = np.asarray(t, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    if t.size == 0:
        return t, y
    order = np.argsort(t)
    t, y = t[order], y[order]
    t_key = np.round(t, 6)
    unique_keys = np.unique(t_key)
    if unique_keys.size == t.size:
        return t, y
    t_out = np.empty(unique_keys.size, dtype=np.float64)
    y_out = np.empty(unique_keys.size, dtype=np.float64)
    for i, key in enumerate(unique_keys):
        mask = t_key == key
        t_out[i] = float(t[mask].mean())
        y_out[i] = float(y[mask].max())
    return t_out, y_out


def _zero_display_height(y_max: float) -> float:
    return max(y_max * 0.06, 0.12)


class DecayCurveWindow(QMainWindow):
    """Independent, draggable window showing photon counts vs delay time."""

    def __init__(self, main_window):
        super().__init__(None)
        self.main_window = main_window
        self.setWindowTitle("FLIMPA — Decay curve")
        self.setWindowFlags(
            Qt.Window | Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint
        )
        self.setAttribute(Qt.WA_QuitOnClose, False)
        self.setMinimumSize(420, 320)
        self.resize(520, 380)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.info_label = QLabel("Select Instruments → Inspect pixel, then click on the image.")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: rgb(200, 200, 200); padding: 4px;")
        layout.addWidget(self.info_label)

        self.figure = Figure(figsize=(5, 3.2), dpi=100, facecolor=_BG)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas, stretch=1)

        controls = QHBoxLayout()
        self.log_check = QCheckBox("Log scale (Y)")
        self.log_check.setStyleSheet("color: white;")
        self.log_check.toggled.connect(self._redraw_last)
        controls.addWidget(self.log_check)

        self.show_fit_check = QCheckBox("Show fit (1 exp)")
        self.show_fit_check.setStyleSheet("color: white;")
        self.show_fit_check.setChecked(True)
        self.show_fit_check.toggled.connect(self._redraw_last)
        controls.addWidget(self.show_fit_check)

        self.show_map_tau_check = QCheckBox("Show map τ curve")
        self.show_map_tau_check.setStyleSheet("color: white;")
        self.show_map_tau_check.setChecked(True)
        self.show_map_tau_check.setToolTip(
            "Overlay 1-exp model using τ from the lifetime map (phasor analysis at this pixel)."
        )
        self.show_map_tau_check.toggled.connect(self._redraw_last)
        controls.addWidget(self.show_map_tau_check)
        controls.addStretch(1)
        layout.addLayout(controls)

        self._last_decay: PixelDecay | None = None
        self._last_fit: DecayFitResult | None = None
        self._plot_ax = None
        self._cursor_vline = None
        self._cursor_label = None
        self._cursor_active = False
        self._cursor_cids: list[int] = []
        self._data_xlim: tuple[float, float] | None = None
        self._data_ylim: tuple[float, float] | None = None
        self._t_min_ns: float | None = None
        self._t_max_ns: float | None = None
        self._connect_cursor_handlers()
        self._draw_empty_axes()

    def _connect_cursor_handlers(self):
        self._disconnect_cursor_handlers()
        self._cursor_cids = [
            self.canvas.mpl_connect("button_press_event", self._on_cursor_press),
            self.canvas.mpl_connect("motion_notify_event", self._on_cursor_motion),
            self.canvas.mpl_connect("button_release_event", self._on_cursor_release),
            self.canvas.mpl_connect("axes_leave_event", self._on_cursor_leave),
        ]

    def _disconnect_cursor_handlers(self):
        for cid in self._cursor_cids:
            try:
                self.canvas.mpl_disconnect(cid)
            except Exception:
                pass
        self._cursor_cids = []

    def _clear_time_cursor(self):
        for artist in (self._cursor_vline, self._cursor_label):
            if artist is not None:
                try:
                    artist.remove()
                except Exception:
                    pass
        self._cursor_vline = None
        self._cursor_label = None

    def _lock_plot_limits(self):
        if self._plot_ax is None:
            return
        if self._data_xlim is not None:
            self._plot_ax.set_xlim(self._data_xlim)
        if self._data_ylim is not None:
            self._plot_ax.set_ylim(self._data_ylim)

    def _store_plot_limits(self, ax):
        self._data_xlim = ax.get_xlim()
        self._data_ylim = ax.get_ylim()
        ax.set_autoscale_on(False)

    def _delay_percent(self, x_ns: float) -> float:
        if self._t_min_ns is None or self._t_max_ns is None:
            return 0.0
        span = self._t_max_ns - self._t_min_ns
        if span <= 0:
            return 0.0
        return float(np.clip((x_ns - self._t_min_ns) / span * 100.0, 0.0, 100.0))

    def _update_time_cursor(self, x_ns: float):
        if self._plot_ax is None:
            return
        ax = self._plot_ax
        self._clear_time_cursor()

        pct = self._delay_percent(x_ns)
        self._cursor_vline = ax.axvline(
            x_ns, color=_CURSOR_COLOR, linestyle=":", linewidth=1.4, zorder=15,
        )
        self._cursor_label = ax.annotate(
            f"{pct:.1f}%",
            xy=(x_ns, 1.0),
            xycoords=("data", "axes fraction"),
            xytext=(-10, -6),
            textcoords="offset points",
            ha="right",
            va="top",
            color=_CURSOR_COLOR,
            fontsize=9,
            fontweight="bold",
            annotation_clip=True,
            bbox=dict(boxstyle="round,pad=0.25", facecolor=(0.1, 0.1, 0.1, 0.85), edgecolor=_CURSOR_COLOR),
            zorder=20,
        )
        self._lock_plot_limits()
        self.canvas.draw_idle()

    def _cursor_event_ax(self, event):
        if self._plot_ax is None:
            return None
        if event.inaxes is self._plot_ax:
            return self._plot_ax
        return None

    def _on_cursor_press(self, event):
        if self._cursor_event_ax(event) is not None and event.button == 1 and event.xdata is not None:
            self._cursor_active = True
            self._update_time_cursor(float(event.xdata))

    def _on_cursor_motion(self, event):
        ax = self._cursor_event_ax(event)
        if ax is None or event.xdata is None:
            return
        if self._cursor_active or (event.button == 1):
            self._update_time_cursor(float(event.xdata))

    def _on_cursor_release(self, event):
        self._cursor_active = False

    def _on_cursor_leave(self, event):
        if event.inaxes is self._plot_ax:
            self._cursor_active = False
            self._clear_time_cursor()
            self.canvas.draw_idle()

    def show_and_raise(self, *, activate: bool = True):
        if not self.isVisible():
            self.show()
        self.raise_()
        if activate:
            self.activateWindow()

    def show_pixel(self, x_click: float, y_click: float, display_shape: tuple[int, int] | None):
        filename = self.main_window.shared_info.config.get("selected_file")
        decay = get_pixel_decay(filename, x_click, y_click, display_shape)
        if decay is None:
            self.info_label.setText("No data loaded for the selected file.")
            self._draw_empty_axes()
            self.show_and_raise(activate=False)
            return
        self._last_decay = decay
        self._redraw_last()
        self.show_and_raise(activate=False)

    def _redraw_last(self):
        if self._last_decay is not None:
            self._plot_decay(self._last_decay)

    def _draw_empty_axes(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        self._plot_ax = ax
        ax.set_facecolor(_BG)
        ax.tick_params(colors="white", labelsize=8)
        ax.set_xlabel("Time (ns)", color="white", fontsize=9)
        ax.set_ylabel("Photon counts", color="white", fontsize=9)
        ax.set_title("Decay curve", color="white", fontsize=10)
        for spine in ax.spines.values():
            spine.set_color("white")
        self._clear_time_cursor()
        self.figure.tight_layout()
        self._store_plot_limits(ax)
        self.canvas.draw_idle()

    def _plot_decay(self, decay: PixelDecay):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        self._plot_ax = ax
        ax.set_facecolor(_BG)

        t = np.asarray(decay.t_ns, dtype=np.float64)
        y = np.asarray(decay.counts, dtype=np.float64)
        t, y = _aggregate_max_per_time(t, y)
        use_log = self.log_check.isChecked() and np.any(y > 0)

        self._last_fit = fit_single_exponential(t, y, tau_hint_ns=decay.tau_ns)
        fit = self._last_fit

        if use_log:
            pos = y > 0
            ax.semilogy(
                t[pos], y[pos], linestyle="none", marker="o",
                color=_TEAL, markersize=4, label="Measured",
            )
            ax.set_ylabel("Photon counts (log)", color="white", fontsize=9)
        else:
            y_max = float(np.max(y)) if y.size else 0.0
            y_top = max(y_max * 1.15, 0.5)
            zero_h = _zero_display_height(y_top)

            pos = y > 0
            zero = y == 0
            if np.any(pos):
                ax.plot(
                    t[pos], y[pos], linestyle="none", marker="o",
                    color=_TEAL, markersize=4, label="Measured",
                )
            if np.any(zero):
                ax.plot(
                    t[zero], np.full(np.sum(zero), zero_h), linestyle="none", marker="o",
                    color=_ZERO_MARKER_COLOR, markersize=3, alpha=0.55,
                    markerfacecolor=_ZERO_MARKER_COLOR, label="0 counts (raised)",
                )
            ax.set_ylim(0, y_top)
            ax.set_ylabel("Photon counts", color="white", fontsize=9)

        if fit is not None and self.show_fit_check.isChecked():
            model = np.asarray(fit.model_counts, dtype=np.float64)
            if use_log:
                mpos = model > 0
                ax.semilogy(
                    t[mpos], model[mpos], "-", color=_FIT_COLOR, linewidth=1.8,
                    label=f"Fit τ={fit.tau_ns:.2f} ns",
                )
            else:
                ax.plot(
                    t, model, "-", color=_FIT_COLOR, linewidth=1.8,
                    label=f"Fit τ={fit.tau_ns:.2f} ns",
                )

        map_model = None
        if decay.tau_ns is not None and decay.tau_ns > 0:
            self.show_map_tau_check.setEnabled(True)
            map_model = predict_decay_at_tau(t, y, decay.tau_ns)
        else:
            self.show_map_tau_check.setEnabled(False)

        if map_model is not None and self.show_map_tau_check.isChecked():
            map_model = np.asarray(map_model, dtype=np.float64)
            if use_log:
                mpos = map_model > 0
                ax.semilogy(
                    t[mpos], map_model[mpos], "--", color=_MAP_TAU_COLOR, linewidth=1.6,
                    label=f"Map τ={decay.tau_ns:.2f} ns",
                )
            else:
                ax.plot(
                    t, map_model, "--", color=_MAP_TAU_COLOR, linewidth=1.6,
                    label=f"Map τ={decay.tau_ns:.2f} ns",
                )

        if t.size:
            self._t_min_ns = float(t.min())
            self._t_max_ns = float(t.max())
            ax.set_xlim(self._t_min_ns, self._t_max_ns)
        else:
            self._t_min_ns = None
            self._t_max_ns = None

        ax.set_xlabel("Time (ns)", color="white", fontsize=9)
        title = f"{decay.filename}  —  pixel (x={decay.x}, y={decay.y})"
        ax.set_title(title, color="white", fontsize=9)
        ax.tick_params(colors="white", labelsize=8)
        for spine in ax.spines.values():
            spine.set_color("white")
        ax.legend(facecolor=(0.25, 0.25, 0.25), edgecolor="white", labelcolor="white", fontsize=8)
        ax.grid(True, alpha=0.2, color="gray")

        parts = [
            f"Σ photons = {decay.total_photons:,}",
            f"avg / channel = {decay.total_photons / max(len(y), 1):.1f}",
        ]
        if decay.tau_ns is not None:
            parts.append(f"τ map ≈ {decay.tau_ns:.2f} ns")
        if fit is not None:
            parts.append(f"fit τ = {fit.tau_ns:.2f} ns")
            parts.append(f"χ²ᵣ = {fit.chi2_reduced:.2f}")
            parts.append(fit.message)
        if decay.baseline_corrected:
            parts.append("baseline corrected")
        if decay.masked_out:
            parts.append("outside mask or zero signal")
        if decay.total_photons < 500:
            parts.append("single-pixel curve is sparse — try Log scale or a brighter pixel")
        parts.append("click & drag: delay as % of window (0% = left, 100% = right)")
        self.info_label.setText("  |  ".join(parts))

        self._clear_time_cursor()
        self.figure.tight_layout()
        self._store_plot_limits(ax)
        self.canvas.draw_idle()
