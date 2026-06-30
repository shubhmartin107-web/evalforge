"""Tests for pass@k and pass^k metrics."""

import pytest
from evalforge.core.metrics import (
    compute_pass_at_k,
    compute_pass_power_k,
    compute_trial_metrics,
)
from evalforge.models import RunMetrics


class TestPassAtK:
    def test_pass_at_1_all_success(self):
        assert compute_pass_at_k([True, True, True], k=1) == 1.0

    def test_pass_at_1_no_success(self):
        assert compute_pass_at_k([False, False, False], k=1) == 0.0

    def test_pass_at_5_mixed(self):
        result = compute_pass_at_k([True, False, False, False, False], k=1)
        assert result == pytest.approx(0.2, rel=1e-6)

    def test_pass_at_k_empty(self):
        assert compute_pass_at_k([], k=5) == 0.0

    def test_pass_at_3_with_success(self):
        result = compute_pass_at_k([True, False, False], k=3)
        assert result > 0

    def test_pass_power_3_all_success(self):
        assert compute_pass_power_k([True, True, True], k=3) == 1.0

    def test_pass_power_3_one_fail(self):
        assert compute_pass_power_k([True, True, False], k=3) == 0.0

    def test_pass_power_k_empty(self):
        assert compute_pass_power_k([], k=3) == 0.0

    def test_pass_power_3_two_of_three(self):
        result = compute_pass_power_k([True, True, True, False], k=3)
        assert result > 0

    def test_trial_metrics_basic(self):
        runs = [
            RunMetrics(success=True, success_score=0.9, total_cost_usd=0.01),
            RunMetrics(success=False, success_score=0.3, total_cost_usd=0.02),
            RunMetrics(success=True, success_score=0.8, total_cost_usd=0.01),
        ]
        result = compute_trial_metrics(runs)
        assert result["n_trials"] == 3
        assert result["n_successes"] == 2
        assert result["avg_score"] == pytest.approx(2.0 / 3.0)
        assert result["pass_at_1"] > 0
        assert result["total_cost"] == 0.04

    def test_trial_metrics_empty(self):
        assert compute_trial_metrics([]) == {}

    def test_trial_metrics_single(self):
        runs = [RunMetrics(success=True, success_score=1.0, total_cost_usd=0.01)]
        result = compute_trial_metrics(runs)
        assert result["n_trials"] == 1
        assert result["pass_at_1"] == 1.0



