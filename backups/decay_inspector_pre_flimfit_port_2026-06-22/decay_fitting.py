"""
Single-exponential decay fitting for the pixel decay inspector.

Ports the FLIMfit TCSPC model (IRF reconvolution + Poisson deviance) from
estimate_irf.m / FLIMGlobalFitController.cpp in simplified form for one ROI/pixel.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize

from utils.shared_data import SharedData

_MIN_TAU_NS = 0.15
_MAX_TAU_NS = 50.0


def _tau_search_range(
    tau_hint_ns: float | None,
    shared: SharedData,
) -> tuple[float, float, float]:
    """Bounds and starting τ (ns) using map/reference lifetime when available."""
    ref_lt = float(shared.config.get("ref_lifetime", 4) or 4)
    hint = tau_hint_ns if tau_hint_ns is not None and tau_hint_ns > 0 and np.isfinite(tau_hint_ns) else ref_lt
    hint = float(np.clip(hint, 0.2, _MAX_TAU_NS))
    tau_min = max(_MIN_TAU_NS, hint * 0.1)
    tau_max = min(_MAX_TAU_NS, max(hint * 5.0, tau_min * 4.0))
    return tau_min, tau_max, hint


@dataclass
class DecayFitResult:
  """Fitted single-exponential decay at one pixel."""

  tau_ns: float
  amplitude: float  # peak height A in y = A·h(t), h max = 1
  offset: float
  chi2_reduced: float
  model_counts: np.ndarray
  used_irf: bool
  converged: bool
  message: str = ""


def _reference_irf(shared: SharedData) -> tuple[np.ndarray, np.ndarray] | None:
  """Instrument response from the loaded reference sample (summed over space)."""
  ref_name = shared.config.get("ref_file")
  if not ref_name or ref_name not in shared.ref_files_dict:
    return None
  entry = shared.ref_files_dict[ref_name]
  ref_data = np.asarray(entry.get("ref_data"), dtype=np.float64)
  t_series = np.asarray(entry.get("t_series"), dtype=np.float64)
  if ref_data.size == 0 or t_series.size == 0:
    return None
  if ref_data.ndim == 3:
    irf = ref_data.sum(axis=(1, 2))
  else:
    irf = ref_data.ravel()
  irf = np.maximum(irf, 0.0)
  if irf.sum() <= 0:
    return None
  return t_series, irf / irf.sum()


def _align_irf(t_sample_s: np.ndarray, t_irf_s: np.ndarray, irf: np.ndarray) -> np.ndarray:
  """Resample IRF onto the sample delay-time grid."""
  if t_irf_s.size == t_sample_s.size and np.allclose(t_irf_s, t_sample_s, rtol=0, atol=1e-12):
    return irf.astype(np.float64)
  return np.interp(t_sample_s, t_irf_s, irf, left=0.0, right=0.0)


def conv_irf_exponential(t_s: np.ndarray, irf: np.ndarray, tau_s: float) -> np.ndarray:
  """
  Exponential reconvolution with a discrete IRF (FLIMfit estimate_irf.m conv_irf).
  t_s and tau_s in seconds.
  """
  t_s = np.asarray(t_s, dtype=np.float64)
  g = np.asarray(irf, dtype=np.float64)
  if t_s.size < 2 or g.size != t_s.size:
    return np.zeros_like(t_s)
  dt = float(t_s[1] - t_s[0])
  if dt <= 0:
    return np.zeros_like(t_s)
  tg = t_s - t_s[0]
  T = float(t_s[-1] - t_s[0])
  tau_s = max(float(tau_s), 1e-15)

  rhoi = np.exp(tg / tau_s)
  G = np.cumsum(g * rhoi)
  G = np.roll(G, 1)
  G[0] = 0.0
  rho = np.exp(dt / tau_s)
  A = tau_s**2 / dt * (1.0 - rho) ** 2 / rho
  B = tau_s**2 / dt * (dt / tau_s - 1.0 + 1.0 / rho)
  C = A * G + B * g * rhoi
  denom = np.exp(T / tau_s) - 1.0
  if abs(denom) < 1e-30:
    f = 0.0
  else:
    f = 1.0 / denom
  return (C + f * C[-1]) / rhoi / tau_s * dt


def _decay_shape_peak_normalized(
  t_s: np.ndarray,
  tau_s: float,
  *,
  used_irf: bool,
  irf_on_grid: np.ndarray | None,
) -> np.ndarray | None:
  """
  Unit peak reconvolved shape h(t; τ) with max(h) = 1.

  Amplitude A in y(t) = A·h(t) is then the model height at the first maximum
  (FLIMfit solves scale separately via I = dc\\d on the unscaled shape).
  """
  tau_s = max(float(tau_s), 1e-15)
  if used_irf and irf_on_grid is not None:
    kernel = conv_irf_exponential(t_s, irf_on_grid, tau_s)
    kernel = np.maximum(kernel, 0.0)
  else:
    tg = t_s - t_s[0]
    T = float(t_s[-1] - t_s[0])
    kernel = np.exp(-tg / tau_s)
    norm = 1.0 - np.exp(-T / tau_s)
    if norm <= 1e-30:
      kernel = np.ones_like(t_s, dtype=np.float64)
    else:
      kernel = kernel / norm
  peak = float(kernel.max())
  if peak <= 0:
    return None
  return kernel / peak


def _optimal_amplitude(counts: np.ndarray, shape: np.ndarray) -> float:
  """Linear least-squares scale: A = argmin ||y - A·shape||² (FLIMfit I = dc\\d)."""
  shape = np.asarray(shape, dtype=np.float64)
  counts = np.asarray(counts, dtype=np.float64)
  denom = float(np.dot(shape, shape))
  if denom <= 0:
    return max(float(counts.max()), 0.0)
  return max(float(np.dot(counts, shape) / denom), 0.0)


def _model_no_irf(t_s: np.ndarray, tau_s: float, amplitude: float, offset: float) -> np.ndarray:
  """Fallback: pulsed-window exponential; amplitude scales peak-normalised shape."""
  shape = _decay_shape_peak_normalized(t_s, tau_s, used_irf=False, irf_on_grid=None)
  if shape is None:
    return np.zeros_like(t_s)
  return amplitude * shape + offset


def _model_with_irf(t_s: np.ndarray, irf: np.ndarray, tau_s: float, amplitude: float, offset: float) -> np.ndarray:
  shape = _decay_shape_peak_normalized(t_s, tau_s, used_irf=True, irf_on_grid=irf)
  if shape is None:
    return _model_no_irf(t_s, tau_s, amplitude, offset)
  return amplitude * shape + offset


def _poisson_deviance(observed: np.ndarray, expected: np.ndarray) -> float:
  """FLIMfit-style reduced Poisson deviance (estimate_irf.m)."""
  obs = np.asarray(observed, dtype=np.float64)
  exp = np.maximum(np.asarray(expected, dtype=np.float64), 1e-12)
  valid = obs > 0
  if not np.any(valid):
    return float(np.sum((obs - exp) ** 2))
  term = obs[valid] * np.log(exp[valid] / obs[valid])
  chi2 = -2.0 * (np.sum(obs - exp) + np.sum(term))
  return float(max(chi2, 0.0))


def _estimate_tau_tcspc(t_s: np.ndarray, counts: np.ndarray) -> float:
  """Mean-lifetime seed from FLIMGlobalFitController.cpp (TCSPC branch)."""
  y = np.maximum(np.asarray(counts, dtype=np.float64), 0.0)
  t = np.asarray(t_s, dtype=np.float64)
  n = y.sum()
  if n <= 0 or t.size < 2:
    return 2.0e-9
  t0 = t[0]
  T = t[-1] - t0
  if T <= 0:
    return 2.0e-9
  t_mean = np.sum(y * (t - t0)) / n / T
  tau = max(float(t_mean), 1e-12)
  for _ in range(5):
    e = np.exp(1.0 / tau)
    iem1 = 1.0 / (e - 1.0)
    denom = e * iem1 * iem1 / (tau * tau) - 1.0
    if abs(denom) < 1e-30:
      break
    tau = tau - (-tau + t_mean + iem1) / denom
    tau = max(tau, 1e-12)
  return tau * T


def _prepare_forward_context(
  t_ns: np.ndarray,
  shared: SharedData,
) -> tuple[np.ndarray, bool, np.ndarray | None]:
  t_s = np.asarray(t_ns, dtype=np.float64) * 1e-9
  irf_info = _reference_irf(shared)
  used_irf = False
  irf_on_grid: np.ndarray | None = None
  if irf_info is not None:
    t_irf_s, irf = irf_info
    irf_on_grid = _align_irf(t_s, t_irf_s, irf)
    if irf_on_grid.sum() > 0:
      irf_on_grid = irf_on_grid / irf_on_grid.sum()
      used_irf = True
  return t_s, used_irf, irf_on_grid


def _forward_model(
  t_s: np.ndarray,
  tau_ns: float,
  counts: np.ndarray,
  offset: float,
  *,
  used_irf: bool,
  irf_on_grid: np.ndarray | None,
) -> tuple[np.ndarray, float] | tuple[None, float]:
  tau_s = max(float(tau_ns) * 1e-9, 1e-15)
  shape = _decay_shape_peak_normalized(t_s, tau_s, used_irf=used_irf, irf_on_grid=irf_on_grid)
  if shape is None:
    return None, 0.0
  amp = _optimal_amplitude(counts, shape)
  return amp * shape + offset, amp


def predict_decay_at_tau(
  t_ns: np.ndarray,
  counts: np.ndarray,
  tau_ns: float,
  *,
  shared: SharedData | None = None,
) -> np.ndarray | None:
  """
  Model decay for a fixed τ (e.g. lifetime-map value), scaled to the measured total photons.
  Uses the same IRF reconvolution as the fitter when a reference is loaded.
  """
  t_ns = np.asarray(t_ns, dtype=np.float64)
  counts = np.asarray(counts, dtype=np.float64)
  if t_ns.size != counts.size or t_ns.size < 2:
    return None
  if counts.sum() <= 0 or tau_ns <= 0 or not np.isfinite(tau_ns):
    return None
  shared = shared or SharedData()
  t_s, used_irf, irf_on_grid = _prepare_forward_context(t_ns, shared)
  out = _forward_model(
    t_s, float(tau_ns), counts, 0.0,
    used_irf=used_irf, irf_on_grid=irf_on_grid,
  )
  if out[0] is None:
    return None
  return out[0]


def fit_single_exponential(
  t_ns: np.ndarray,
  counts: np.ndarray,
  *,
  fit_offset: bool = False,
  tau_hint_ns: float | None = None,
  shared: SharedData | None = None,
) -> DecayFitResult | None:
  """
  Fit one single-exponential decay with optional IRF from the reference file.

  Uses Poisson deviance like FLIMfit; IRF is taken from ref_files_dict when set.
  """
  t_ns = np.asarray(t_ns, dtype=np.float64)
  counts = np.asarray(counts, dtype=np.float64)
  if t_ns.size != counts.size or t_ns.size < 4:
    return None
  if counts.sum() <= 0:
    return None

  shared = shared or SharedData()
  t_s, used_irf, irf_on_grid = _prepare_forward_context(t_ns, shared)

  total = float(counts.sum())
  tau0_s = _estimate_tau_tcspc(t_s, counts)
  tau0_ns = float(np.clip(tau0_s * 1e9, _MIN_TAU_NS, _MAX_TAU_NS))
  tau_min, tau_max, hint_ns = _tau_search_range(tau_hint_ns, shared)

  n_params = 2 if fit_offset else 1

  def model_at_tau(tau_ns: float, offset: float = 0.0) -> tuple[np.ndarray, float] | tuple[None, float]:
    return _forward_model(
      t_s, tau_ns, counts, offset,
      used_irf=used_irf, irf_on_grid=irf_on_grid,
    )

  def objective(x: np.ndarray) -> float:
    tau_ns = float(np.clip(x[0], tau_min, tau_max))
    offset = float(np.exp(x[1])) if fit_offset else 0.0
    model, _ = model_at_tau(tau_ns, offset)
    if model is None:
      return np.inf
    return _poisson_deviance(counts, model) / max(len(counts) - n_params, 1)

  starts = [hint_ns, tau0_ns, (tau_min + tau_max) / 2.0]
  starts = [float(np.clip(s, tau_min, tau_max)) for s in starts]

  best_res = None
  best_obj = np.inf
  for tau_start in dict.fromkeys(round(s, 4) for s in starts):
    x0 = np.array([tau_start] + ([np.log(0.5)] if fit_offset else []), dtype=np.float64)
    bounds = [(tau_min, tau_max)]
    if fit_offset:
      bounds.append((np.log(1e-3), np.log(max(total, 1.0))))
    res = minimize(objective, x0, method="L-BFGS-B", bounds=bounds)
    if float(res.fun) < best_obj:
      best_obj = float(res.fun)
      best_res = res

  res = best_res
  if res is None:
    return None

  tau_fit = float(np.clip(res.x[0], tau_min, tau_max))
  offset_fit = float(np.exp(res.x[1])) if fit_offset else 0.0
  model, amp_fit = model_at_tau(tau_fit, offset_fit)
  if model is None:
    return None
  chi2 = _poisson_deviance(counts, model) / max(len(counts) - n_params, 1)

  msg = "IRF from reference" if used_irf else "no IRF — exponential only (load reference for FLIMfit-style fit)"
  msg += f"; A≈peak ({amp_fit:.1f} cts at model max)"
  if total < 150:
    msg += "; sparse pixel — fit may differ from τ map"
  if tau_hint_ns is not None and tau_hint_ns > 0:
    msg += f"; search centred on map τ≈{tau_hint_ns:.2f} ns"
  return DecayFitResult(
    tau_ns=tau_fit,
    amplitude=amp_fit,
    offset=offset_fit,
    chi2_reduced=chi2,
    model_counts=model,
    used_irf=used_irf,
    converged=bool(res.success),
    message=msg,
  )
