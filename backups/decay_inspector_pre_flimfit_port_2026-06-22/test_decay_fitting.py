"""Tests for FLIMfit-style single-exponential decay fitting."""

import numpy as np

from utils.decay_fitting import (
    conv_irf_exponential,
    fit_single_exponential,
    predict_decay_at_tau,
    _decay_shape_peak_normalized,
)
from utils.shared_data import SharedData


def test_conv_irf_exponential_positive():
    t = np.linspace(0, 10e-9, 64)
    irf = np.zeros_like(t)
    irf[5] = 1.0
    kernel = conv_irf_exponential(t, irf, 2e-9)
    assert kernel.shape == t.shape
    assert np.all(kernel >= 0)
    assert kernel.sum() > 0


def test_fit_recovers_tau_without_irf():
    shared = SharedData()
    shared.ref_files_dict.clear()

    t_ns = np.linspace(0, 20, 80)
    t_s = t_ns * 1e-9
    tau_true_s = 3.0e-9
    shape = _decay_shape_peak_normalized(t_s, tau_true_s, used_irf=False, irf_on_grid=None)
    assert shape is not None
    counts = (40.0 * shape).astype(np.float64)
    counts += np.random.default_rng(0).poisson(0.2, size=counts.shape)

    fit = fit_single_exponential(t_ns, counts, shared=shared)
    assert fit is not None
    assert abs(fit.tau_ns - tau_true_s * 1e9) < 1.5
    assert fit.model_counts.shape == counts.shape
    assert abs(fit.amplitude - counts.max()) < 15.0


def test_fit_uses_reference_irf():
    shared = SharedData()
    shared.ref_files_dict.clear()

    t_s = np.linspace(0, 20e-9, 80)
    t_ns = t_s * 1e9
    irf = np.zeros(80)
    irf[4:8] = [1, 3, 2, 1]
    shared.ref_files_dict["ref"] = {"ref_data": irf.reshape(80, 1, 1), "t_series": t_s}
    shared.config["ref_file"] = "ref"

    tau_true_s = 2.5e-9
    irf_norm = irf / irf.sum()
    shape = _decay_shape_peak_normalized(t_s, tau_true_s, used_irf=True, irf_on_grid=irf_norm)
    assert shape is not None
    counts = (55.0 * shape).astype(np.float64)

    fit = fit_single_exponential(t_ns, counts, shared=shared)
    assert fit is not None
    assert fit.used_irf is True
    assert abs(fit.tau_ns - tau_true_s * 1e9) < 1.5


def test_predict_decay_at_tau_matches_fit_at_same_tau():
    shared = SharedData()
    shared.ref_files_dict.clear()

    t_ns = np.linspace(0, 20, 80)
    t_s = t_ns * 1e-9
    tau_true_s = 3.0e-9
    shape = _decay_shape_peak_normalized(t_s, tau_true_s, used_irf=False, irf_on_grid=None)
    assert shape is not None
    counts = (40.0 * shape).astype(np.float64)

    predicted = predict_decay_at_tau(t_ns, counts, tau_true_s * 1e9, shared=shared)
    assert predicted is not None
    assert predicted.shape == counts.shape
    assert abs(predicted.max() - counts.max()) < 2.0
