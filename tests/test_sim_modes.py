"""Tests for simulation mode helpers."""

from src.sim import Config, initialize_user_state, should_reset_none_feedback, validate_config
from src.utils import setup_rng


def make_cfg(**overrides):
    """Build a minimal valid config for helper tests."""
    data = dict(
        seed=1,
        scenario="therapy",
        episodes=4,
        memory_mode="none",
        token_budget=6000,
        alpha=0.12,
        beta=0.072,
        noise_sigma=0.01,
        assistant_model="gpt-4o-mini",
        user_model="gpt-4o-mini",
        summary_bullets_max=5,
        summary_update_temperature=0.2,
        log_dir="data/logs",
    )
    data.update(overrides)
    return Config(**data)


def test_initialize_user_state_fixed_binary_assignment():
    """Fixed-binary mode should assign deterministic user types by episode parity."""
    cfg = make_cfg(
        dynamics_mode="fixed_binary",
        fixed_d_vulnerable=0.95,
        fixed_d_not_vulnerable=0.1,
    )
    rng = setup_rng(1)
    d0, t0 = initialize_user_state(cfg, 0, rng)
    d1, t1 = initialize_user_state(cfg, 1, rng)
    d2, t2 = initialize_user_state(cfg, 2, rng)

    assert (d0, t0) == (0.95, "vulnerable")
    assert (d1, t1) == (0.1, "not_vulnerable")
    assert (d2, t2) == (0.95, "vulnerable")


def test_initialize_user_state_dynamic():
    """Dynamic mode should return stochastic D and dynamic user type."""
    cfg = make_cfg(dynamics_mode="dynamic")
    rng = setup_rng(42)
    d, user_type = initialize_user_state(cfg, 0, rng)

    assert 0.0 <= d <= 1.0
    assert user_type == "dynamic"


def test_should_reset_none_feedback():
    """None-feedback reset only applies at conversation starts when enabled."""
    cfg = make_cfg(memory_mode="none", none_reset_feedback_at_conversation_start=True)
    assert should_reset_none_feedback(cfg, conversation_id=1, step=0)
    assert not should_reset_none_feedback(cfg, conversation_id=1, step=1)
    assert not should_reset_none_feedback(cfg, conversation_id=0, step=0)

    cfg.memory_mode = "summary"
    assert not should_reset_none_feedback(cfg, conversation_id=1, step=0)


def test_validate_config_rejects_invalid_values():
    """Config validator should reject malformed ranges."""
    bad_temp = make_cfg(assistant_temperature=3.0)
    try:
        validate_config(bad_temp)
    except ValueError as e:
        assert "assistant_temperature" in str(e)
    else:
        raise AssertionError("Expected ValueError for invalid assistant_temperature")

    bad_history = make_cfg(summary_update_history_k=-1)
    try:
        validate_config(bad_history)
    except ValueError as e:
        assert "summary_update_history_k" in str(e)
    else:
        raise AssertionError("Expected ValueError for invalid summary_update_history_k")
