import pytest
from scipy.interpolate import CubicSpline
from src.exo.assistance_calculator import AssistanceCalculator
from settings.constants import INCLINE_WALK_TIMINGS
import numpy as np

@pytest.fixture
def generator():
    """
    Fixture to create a default AssistanceCalculator instance for use in tests.
    """
    return AssistanceCalculator(
        t_rise=10,
        t_peak=30,
        t_fall=15,
        holding_torque=0.1,
        resolution=1000
    )


def test_set_new_timing_params(generator):
    """
    Test that set_new_timing_params correctly updates timing parameters.
    """
    generator.set_new_timing_params(12, 35, 18)
    assert generator.t_rise == 12
    assert generator.t_peak == 35
    assert generator.t_fall == 18


def test_set_new_holding_torque(generator):
    """
    Test that set_new_holding_torque correctly updates the holding torque value.
    """
    generator.set_new_holding_torque(0.25)
    assert generator.holding_torque == 0.25


def test_convert_params_to_percent_stride():
    """
    Test that timing parameters are converted to percent stride correctly.
    """
    gen = AssistanceCalculator(10, 40, 20, 0.1)
    assert pytest.approx(gen.t_peak, 0.01) == 0.4
    assert pytest.approx(gen.t_rise, 0.01) == 0.1
    assert pytest.approx(gen.t_fall, 0.01) == 0.2


def test_calculate_onset_and_dropoff_times():
    """
    Test that onset and dropoff times are calculated correctly from timing parameters.
    """
    gen = AssistanceCalculator(10, 40, 20, 0.1)
    expected_onset = 0.4 - 0.1
    expected_dropoff = 0.4 + 0.2
    assert pytest.approx(gen.t_onset, 0.01) == expected_onset
    assert pytest.approx(gen.t_dropoff, 0.01) == expected_dropoff


def test_create_spline_sections(generator):
    """
    Test that create_spline_sections returns valid CubicSpline objects for rising and falling sections.
    """
    rise, fall = generator.create_spline_sections()
    assert isinstance(rise, CubicSpline)
    assert isinstance(fall, CubicSpline)


def test_create_normalized_profile(generator):
    """
    Test that create_normalized_profile creates a normalized profile of the correct length.
    """
    rise, fall = generator.create_spline_sections()
    generator.create_normalized_profile(rise, fall)
    assert len(generator.normalized_profile) == generator.resolution


def test_get_normalized_torque_command(generator):
    """
    Test that get_normalized_torque_command returns a float torque value for a given percent_stride.
    """
    generator.percent_stride = 0.5
    torque = generator.get_normalized_torque_command()
    assert isinstance(torque, float)


def test_scale_to_peak_torque(generator):
    """
    Test that scale_to_peak_torque correctly scales a normalized torque to the specified range.
    """
    torque = generator.scale_to_peak_torque(0.5, 0.1, 1.0)
    assert pytest.approx(torque, 0.01) == 0.55


def test_scale_to_peak_torque_manual_equivalence(generator):
    """
    Test that scale_to_peak_torque produces the same result as linearly
    interpolating/scaling torque from [normalize_min, normalize_max]
    to [new_min_torque, new_peak_torque] using numpy's interp function.
    """
    normalized_torque = 0.7
    new_min_torque = 0.2
    new_peak_torque = 1.2

    # Using the method
    method_result = generator.scale_to_peak_torque(normalized_torque, new_min_torque, new_peak_torque)

    # Manual calculation
    input_torque_range = [generator.normalize_min, generator.normalize_max]   # between 0 and 1
    output_torque_range = [new_min_torque, new_peak_torque]                   # between peak torque & holding torque
    manual_result = np.interp(normalized_torque, input_torque_range, output_torque_range)

    assert pytest.approx(method_result, 1e-8) == manual_result


def test_torque_generator_during_swing(generator):
    """
    Test that torque_generator returns holding torque during swing phase.
    """
    torque = generator.torque_generator(current_time=0.5, stride_period=1.0, peak_torque=1.0, in_swing=True)
    assert torque == generator.holding_torque


def test_torque_generator_during_stance(generator):
    """
    Test that torque_generator returns a float torque value during stance phase.
    """
    torque = generator.torque_generator(current_time=0.5, stride_period=1.0, peak_torque=1.0, in_swing=False)
    assert isinstance(torque, float)

# ---------------------
#     EDGE CASES
# ---------------------

def test_zero_stride_period(generator):
    """
    Test that a ZeroDivisionError is raised if stride_period is zero in torque_generator.
    """
    with pytest.raises(ZeroDivisionError):
        generator.torque_generator(current_time=0.5, stride_period=0.0, peak_torque=1.0, in_swing=False)


def test_percent_stride_out_of_bounds(generator):
    """
    Test that get_normalized_torque_command handles percent_stride > 1 by capping to max index and returns a float.
    """
    generator.percent_stride = 1.5
    torque = generator.get_normalized_torque_command()
    assert isinstance(torque, float) # should cap to max index, not raise error


def test_zero_resolution():
    """
    Test that a ValueError is raised if resolution is zero in AssistanceCalculator.
    """
    with pytest.raises(ValueError):
        AssistanceCalculator(10, 30, 15, 0.1, resolution=0)


def test_negative_parameters():
    """
    Test that a ValueError is raised if any timing parameter is negative in AssistanceCalculator.
    """
    with pytest.raises(ValueError):
        AssistanceCalculator(-10, -30, -15, -0.1)


def test_large_resolution(generator):
    """
    Stress test: Ensure create_normalized_profile works with a very large resolution (500,000 points).
    """
    generator.resolution = 500000  # 500k points
    rise, fall = generator.create_spline_sections()
    generator.create_normalized_profile(rise, fall)
    assert len(generator.normalized_profile) == 500000


def test_dropoff_greater_than_toeoff():
    """
    Test that a ValueError is raised if drop-off time is greater than or equal to toe-off time.
    """
    t_peak = INCLINE_WALK_TIMINGS.P_TOE_OFF - 5
    t_fall = 10  # This will push dropoff past toe-off
    with pytest.raises(ValueError, match="toe-off time"):
        ac = AssistanceCalculator(t_rise=5, t_peak=t_peak, t_fall=t_fall, holding_torque=0.1, resolution=1000)
        ac.calculate_onset_and_dropoff_times()


def test_normalized_profile_range(generator):
    """
    Test that all values in normalized_profile are between 0 and 1 (inclusive).
    """
    for value in generator.normalized_profile.values():
        assert 0.0 <= value <= 1.0


def test_torque_generator_meets_peak_setpoint():
    """
    Test that for multiple peak torque setpoints, the output from torque_generator reaches at least the setpoint.
    """
    gen = AssistanceCalculator(t_rise=10, t_peak=30, t_fall=15, holding_torque=0.1, resolution=1000)
    stride_period = 1.0
    for peak in range(7, 41):  # 7 to 40 Nm
        max_torque = float('-inf')
        for i in range(0, 1000):
            t = i * stride_period / 1000
            torque = gen.torque_generator(current_time=t, stride_period=stride_period, peak_torque=peak, in_swing=False)
            if torque > max_torque:
                max_torque = torque
        assert max_torque >= peak


def test_torque_generator_no_negative_values():
    """
    Test that torque_generator never outputs negative values. If a negative value is generated, a ValueError should be raised and holding torque used instead.
    """
    gen = AssistanceCalculator(t_rise=10, t_peak=30, t_fall=15, holding_torque=0.1, resolution=1000)
    stride_period = 1.0
    for peak in range(7, 41):
        for i in range(0, 1000):
            t = i * stride_period / 1000
            torque = gen.torque_generator(current_time=t, stride_period=stride_period, peak_torque=peak, in_swing=False)
            assert torque >= 0.0