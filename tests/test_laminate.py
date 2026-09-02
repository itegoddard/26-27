"""Sandwich section stiffness."""

import pytest

from goddard.structures import laminate as lam

# Representative CF/foam fin. Every one of these is an OPEN register parameter
# (I1-I5) -- they exist here to exercise the maths, not as design values.
CF_E = 70e9      # Pa, quasi-isotropic carbon laminate
CF_G = 5e9       # Pa
FOAM_E = 100e6   # Pa
FOAM_G = 40e6    # Pa


def section(**kw):
    base = dict(
        face_thickness_m=0.0005,
        core_thickness_m=0.004,
        chord_m=0.20,
        face_modulus_Pa=CF_E,
        face_shear_Pa=CF_G,
        core_modulus_Pa=FOAM_E,
        core_shear_Pa=FOAM_G,
    )
    base.update(kw)
    return lam.SandwichSection(**base)


def test_geometry_properties():
    s = section()
    assert s.total_thickness_m == pytest.approx(0.005)
    assert s.face_separation_m == pytest.approx(0.0045)


def test_solid_plate_torsion_constant():
    """J = c t^3 / 3 for a thin plate."""
    assert lam.torsion_constant_solid(0.2, 0.005) == pytest.approx(
        0.2 * 0.005 ** 3 / 3.0
    )


def test_recovers_solid_plate_when_faces_carry_everything():
    """Degenerate check on the GJ = 4 c D_xy relation.

    Collapse the sandwich to a solid plate of thickness t by setting the core to
    the same material as the faces and zero face thickness, and the torsional
    rigidity must reduce to the classical G c t^3 / 3.
    """
    t = 0.005
    s = section(
        face_thickness_m=1e-12,
        core_thickness_m=t,
        core_modulus_Pa=CF_E,
        core_shear_Pa=CF_G,
    )
    assert lam.torsional_stiffness(s) == pytest.approx(
        CF_G * 0.20 * t ** 3 / 3.0, rel=1e-6
    )


def test_foam_core_buys_large_torsional_stiffness():
    """The design rationale for the foam core, quantified.

    Same mass of carbon, but separated by a core rather than stacked solid,
    should be dramatically stiffer in torsion -- GJ scales with the square of
    face separation.
    """
    sandwich = section()
    stacked = section(face_thickness_m=0.0005, core_thickness_m=1e-9)
    assert lam.torsional_stiffness(sandwich) > 50.0 * lam.torsional_stiffness(stacked)


def test_torsional_stiffness_scales_with_face_separation_squared():
    thin = lam.torsional_stiffness(section(core_thickness_m=0.004))
    thick = lam.torsional_stiffness(section(core_thickness_m=0.009))
    # d goes 0.0045 -> 0.0095, so the face term scales by (0.0095/0.0045)**2
    assert thick / thin == pytest.approx((0.0095 / 0.0045) ** 2, rel=0.05)


def test_bending_stiffness_is_positive_and_face_dominated():
    s = section()
    total = lam.bending_stiffness(s)
    core_only = lam.bending_stiffness(section(face_modulus_Pa=1e-9))
    assert total > 0.0
    assert core_only < 0.02 * total


def test_effective_shear_modulus_far_exceeds_raw_core():
    """The equivalent-solid mapping into TN 4197.

    G_eff must land between the core and face shear moduli -- it represents a
    solid plate that twists like the sandwich.
    """
    g_eff = lam.effective_shear_modulus(section())
    assert FOAM_G < g_eff < CF_G


def test_effective_shear_modulus_is_gj_over_j():
    s = section()
    j = lam.torsion_constant_solid(s.chord_m, s.total_thickness_m)
    assert lam.effective_shear_modulus(s) == pytest.approx(
        lam.torsional_stiffness(s) / j
    )


def test_rejects_nonphysical_sections():
    with pytest.raises(ValueError):
        section(face_thickness_m=0.0)
    with pytest.raises(ValueError):
        section(chord_m=-1.0)
    with pytest.raises(ValueError):
        section(core_shear_Pa=-1.0)
    with pytest.raises(ValueError):
        lam.torsion_constant_solid(0.2, 0.0)


# ------------------------------------------- core shear compliance (the fix)


def _fin_section(core_shear_Pa: float) -> lam.SandwichSection:
    """The real fin: 3 plies of +/-45 carbon each side of a foam core."""
    t_face = 3 * 1.981e-4
    return lam.SandwichSection(
        face_thickness_m=t_face,
        core_thickness_m=0.00635 - 2 * t_face,
        chord_m=0.1425,
        face_modulus_Pa=1.733e10,
        face_shear_Pa=3.10e10,
        core_modulus_Pa=core_shear_Pa * 2.5,
        core_shear_Pa=core_shear_Pa,
    )


def test_core_shear_stiffness_closed_form():
    sec = _fin_section(19e6)
    expected = 19e6 * sec.face_separation_m ** 2 / sec.core_thickness_m
    assert lam.core_shear_stiffness(sec) == pytest.approx(expected)


def test_shear_correction_is_between_zero_and_one():
    for g in (1e6, 19e6, 200e6, 5e9):
        k = lam.shear_correction_factor(_fin_section(g), 0.1425)
        assert 0.0 < k <= 1.0


def test_stiffer_core_gives_less_knockdown():
    soft = lam.shear_correction_factor(_fin_section(5e6), 0.1425)
    stiff = lam.shear_correction_factor(_fin_section(200e6), 0.1425)
    assert soft < stiff


def test_correction_tends_to_unity_for_a_very_stiff_core():
    assert lam.shear_correction_factor(_fin_section(1e12), 0.1425) == pytest.approx(
        1.0, abs=1e-3
    )


def test_corrected_gj_is_below_the_upper_bound():
    """The uncorrected value is an upper bound, so the correction must reduce."""
    sec = _fin_section(19e6)
    upper = lam.torsional_stiffness(sec)
    corrected = lam.torsional_stiffness(sec, characteristic_length_m=0.1425)
    assert corrected < upper


def test_the_core_now_actually_changes_the_answer():
    """Regression test for the bug this correction fixes.

    Before core shear compliance was modelled, sweeping the core shear modulus
    from 5 to 200 MPa moved GJ by 0.7 % -- the faces outweighed the core term
    5327:1, so the model was effectively blind to the core it exists to
    evaluate. With the correction the same sweep must move GJ substantially.
    """
    c = 0.1425
    soft = lam.torsional_stiffness(_fin_section(5e6), characteristic_length_m=c)
    stiff = lam.torsional_stiffness(_fin_section(200e6), characteristic_length_m=c)
    assert stiff / soft > 3.0, "core shear compliance is not being felt"


def test_solid_limit_is_unaffected_by_the_correction():
    """Vanishing faces means nothing to shear-lag, so the solid result stands."""
    g, c, t = 5.0e9, 0.20, 0.006
    sec = lam.SandwichSection(
        face_thickness_m=1e-9, core_thickness_m=t, chord_m=c,
        face_modulus_Pa=1.0, face_shear_Pa=1.0,
        core_modulus_Pa=g, core_shear_Pa=g,
    )
    assert lam.torsional_stiffness(sec, characteristic_length_m=c) == pytest.approx(
        g * c * t ** 3 / 3.0, rel=1e-6
    )


def test_rejects_bad_characteristic_length():
    with pytest.raises(ValueError):
        lam.shear_correction_factor(_fin_section(19e6), 0.0)
