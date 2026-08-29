"""Generated report artifacts."""

from __future__ import annotations

import pytest

from goddard import band as band_mod
from goddard import sim as sim_mod
from goddard.report import excel, plots

openpyxl = pytest.importorskip("openpyxl")


@pytest.fixture(scope="module")
def result(request):
    vehicle = request.getfixturevalue("vehicle")
    return sim_mod.run(vehicle, dt=0.05, max_time_s=300.0)


def test_writes_a_workbook_with_the_expected_sheets(vehicle, tmp_path):
    result = sim_mod.run(vehicle, dt=0.1, max_time_s=200.0)
    path = excel.write(result, tmp_path / "out.xlsx")
    assert path.exists()

    wb = openpyxl.load_workbook(path)
    assert {"Summary", "Events", "Trajectory", "Motor"} <= set(wb.sheetnames)


def test_summary_sheet_states_the_target_and_whether_it_was_met(vehicle, tmp_path):
    result = sim_mod.run(vehicle, dt=0.1, max_time_s=200.0)
    wb = openpyxl.load_workbook(excel.write(result, tmp_path / "out.xlsx"))
    text = "\n".join(
        str(c.value)
        for row in wb["Summary"].iter_rows()
        for c in row
        if c.value is not None
    )
    assert "Apogee" in text
    assert "Target" in text
    assert "50000" in text or "50,000" in text


def test_workbook_declares_itself_read_only(vehicle, tmp_path):
    """The workbook is an output. It must say so, on the first sheet."""
    result = sim_mod.run(vehicle, dt=0.1, max_time_s=200.0)
    wb = openpyxl.load_workbook(excel.write(result, tmp_path / "out.xlsx"))
    banner = str(wb["Summary"]["A2"].value)
    assert "DO NOT EDIT" in banner
    assert "config" in banner


def test_warnings_reach_the_report(vehicle, tmp_path):
    """An uncalibrated drag model must not lose its warning in the handoff."""
    result = sim_mod.run(vehicle, dt=0.1, max_time_s=200.0)
    wb = openpyxl.load_workbook(excel.write(result, tmp_path / "out.xlsx"))
    text = "\n".join(
        str(c.value)
        for row in wb["Summary"].iter_rows()
        for c in row
        if c.value is not None
    )
    assert "UNCALIBRATED" in text


def test_trajectory_sheet_is_strided_not_truncated(vehicle, tmp_path):
    result = sim_mod.run(vehicle, dt=0.1, max_time_s=300.0)
    wb = openpyxl.load_workbook(excel.write(result, tmp_path / "o.xlsx", sample_stride=5))
    rows = wb["Trajectory"].max_row - 1  # minus header
    assert rows == pytest.approx(len(result.samples) / 5, rel=0.05)


def test_band_sheet_records_every_corner(vehicle, tmp_path):
    out = band_mod.run_band(vehicle, levels=2, dt=0.2, max_time_s=120.0)
    best = next(c.result for c in out.corners if c.ok)
    wb = openpyxl.load_workbook(
        excel.write(best, tmp_path / "band.xlsx", band=out)
    )
    assert "Band Envelope" in wb.sheetnames
    text = "\n".join(
        str(c.value)
        for row in wb["Band Envelope"].iter_rows()
        for c in row
        if c.value is not None
    )
    assert "apogee_ft" in text
    assert "section 6.1" in text  # the conservatism note must survive


@pytest.mark.skipif(not plots.available(), reason="matplotlib not installed")
def test_plots_are_written(vehicle, tmp_path):
    result = sim_mod.run(vehicle, dt=0.1, max_time_s=200.0)
    written = plots.write(result, tmp_path / "plots")
    assert len(written) >= 7
    assert all(p.exists() and p.stat().st_size > 0 for p in written)
    names = {p.stem for p in written}
    assert {"altitude", "mach", "drag_coefficient", "static_margin"} <= names
