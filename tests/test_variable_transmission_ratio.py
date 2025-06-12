import pytest
import numpy as np
from src.exo.variable_transmission_ratio import VariableTransmissionRatio


def test_tr_minimum_value():
    """
    Test that the transmission ratio (TR) never goes below min_allowable_TR as ankle angle goes from 0 to 180 degrees.
    """
    tr_gen = VariableTransmissionRatio('left')
    for angle in range(-180, 270):
        tr = tr_gen.get_TR(angle)
        assert tr >= tr_gen.min_allowable_TR, f"TR dropped below min_allowable_TR at angle {angle}: {tr}"


def test_tr_angle_to_index_and_index_to_angle():
    """
    Test that angle_to_index and index_to_angle are inverses within tolerance.
    """
    tr_gen = VariableTransmissionRatio('left')
    for angle in np.linspace(tr_gen.min_allowable_angle, tr_gen.max_allowable_angle, 10):
        idx = tr_gen.angle_to_index(angle)
        angle_back = tr_gen.index_to_angle(idx)
        assert np.isclose(angle, angle_back, atol=1e-2), f"angle: {angle}, angle_back: {angle_back}"


def test_tr_offset_property():
    """
    Test that get_offset returns the same value as the offset attribute.
    """
    tr_gen = VariableTransmissionRatio('left')
    assert tr_gen.get_offset() == tr_gen.offset


def test_tr_coefs_loaded():
    """
    Test that TR coefficients and motor curve coefficients are loaded and are lists of floats.
    """
    tr_gen = VariableTransmissionRatio('left')
    assert isinstance(tr_gen.TR_coefs, list)
    assert all(isinstance(x, float) for x in tr_gen.TR_coefs)
    assert isinstance(tr_gen.motor_curve_coefs, list)
    assert all(isinstance(x, float) for x in tr_gen.motor_curve_coefs)


def test_tr_dict_range():
    """
    Test that the TR_dict covers the expected range of indices and values are floats.
    """
    tr_gen = VariableTransmissionRatio('left')
    assert 0 in tr_gen.TR_dict
    assert (tr_gen.granularity - 1) in tr_gen.TR_dict
    for i in [0, tr_gen.granularity // 2, tr_gen.granularity - 1]:
        assert isinstance(tr_gen.TR_dict[i], float)


def test_tr_coefs_file_exists():
    """
    Test that a TR coefs file exists for the default coefs_prefix and filepath.
    """
    from src.settings.constants import TR_COEFS_PREFIX, TR_FOLDER_PATH
    import os
    found = False
    # Defensive: skip if folder does not exist
    if os.path.isdir(TR_FOLDER_PATH):
        for fname in os.listdir(TR_FOLDER_PATH):
            if fname.startswith(TR_COEFS_PREFIX):
                found = True
                break
    assert found, f"No TR coefs file found in {TR_FOLDER_PATH} with prefix {TR_COEFS_PREFIX}"
