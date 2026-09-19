"""tests/test_attacks.py"""
import pytest
from attacks import circuit_kwargs_for


def test_known_modes_resolve():
    for mode in ["clean", "noisy", "intercept_resend", "impersonation"]:
        kwargs = circuit_kwargs_for(mode)
        assert "eve_intercept" in kwargs and "no_entanglement" in kwargs


def test_unknown_mode_raises():
    with pytest.raises(ValueError):
        circuit_kwargs_for("not_a_real_mode")


def test_intercept_resend_and_impersonation_are_distinct_circuits():
    ir = circuit_kwargs_for("intercept_resend")
    imp = circuit_kwargs_for("impersonation")
    assert ir["eve_intercept"] is True and ir["no_entanglement"] is False
    assert imp["eve_intercept"] is False and imp["no_entanglement"] is True
