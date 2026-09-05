"""The config schema and the assumptions register must not drift apart.

If a register entry has no schema field, the model can run while silently
missing it -- which is exactly the failure class the Open sentinel exists to
prevent. If a schema field has no register entry, nobody knows to go and ask
for the number.

This test is the guard. When it fails, fix whichever side is wrong; do not
relax the assertion.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from goddard.config import RocketConfig

REGISTER_CSV = Path(__file__).resolve().parent.parent / "docs" / "assumptions_register.csv"


def _register_rows() -> list[dict[str, str]]:
    if not REGISTER_CSV.exists():
        pytest.skip(f"register CSV not found at {REGISTER_CSV}")
    with REGISTER_CSV.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_every_open_register_entry_has_a_schema_field():
    rows = _register_rows()
    register_open = {r["ID"] for r in rows if r["Status"].startswith("OPEN")}
    schema_ids = {o.register_id for _, o in RocketConfig().missing()}

    missing = sorted(register_open - schema_ids)
    assert not missing, (
        f"register entries with no schema field: {missing}. Add fields to "
        "goddard/config/schema.py or the model will run without them."
    )


def test_every_open_schema_field_has_a_register_entry():
    rows = _register_rows()
    register_open = {r["ID"] for r in rows if r["Status"].startswith("OPEN")}
    schema_ids = {o.register_id for _, o in RocketConfig().missing()}

    extra = sorted(schema_ids - register_open)
    assert not extra, (
        f"schema fields with no OPEN register entry: {extra}. Either the "
        "register says it is filled, or it needs adding to the register."
    )


def test_the_only_placeholder_is_the_known_one():
    """D12, the N2O latent heat, is the single outstanding placeholder.

    G11 (the CEA table) was resolved. D12 was NOT tracked here at all until the
    register was audited against the code -- it claimed zero placeholders while
    props.n2o.enthalpy_vaporisation was raising and goddard_v1 was supplying a
    shaped substitute. A register that does not know what the model is standing
    on is worse than no register.

    Clearing D12 means the verified ESDU 91022 latent-heat coefficients, checked
    against ~376 kJ/kg at the normal boiling point and ~145-150 kJ/kg at 20 C.
    If a NEW placeholder appears, track it here rather than loosening this test.
    """
    rows = _register_rows()
    placeholders = [r["ID"] for r in rows if r["Status"].startswith("PLACEHOLDER")]
    assert placeholders == ["D12"], f"unexpected PLACEHOLDER(s): {placeholders}"


def test_the_three_banded_constants_are_the_expected_ones():
    rows = _register_rows()
    banded = sorted(r["ID"] for r in rows if r["Status"].startswith("BANDED"))
    assert banded == ["E5", "F8", "G9"], (
        "the three unmeasured constants are injector_Cd (E5), "
        "regression_calibration (F8) and eta_cstar (G9)"
    )


def test_confirmed_launch_site_matches_the_register():
    rows = _register_rows()
    a1 = next(r for r in rows if r["ID"] == "A1")
    assert a1["Status"].startswith("CONFIRMED")
    assert "1216" in a1["Current"]
    assert RocketConfig().environment.field_elevation_m == 1216.0
