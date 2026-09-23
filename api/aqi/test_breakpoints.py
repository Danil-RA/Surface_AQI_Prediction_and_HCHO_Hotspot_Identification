"""
Unit tests for api/aqi/breakpoints.py.

Run with:  pytest api/aqi/test_breakpoints.py -v
"""

import pytest
from api.aqi.breakpoints import (
    compute_sub_index,
    compute_aqi,
    compute_all_sub_indices,
    get_category,
    POLLUTANTS,
)


# ---------------------------------------------------------------------------
# get_category
# ---------------------------------------------------------------------------

class TestGetCategory:
    def test_good(self):
        cat = get_category(0)
        assert cat.name == "Good"

    def test_good_upper_bound(self):
        cat = get_category(50)
        assert cat.name == "Good"

    def test_satisfactory(self):
        cat = get_category(51)
        assert cat.name == "Satisfactory"
        cat2 = get_category(100)
        assert cat2.name == "Satisfactory"

    def test_moderate(self):
        assert get_category(101).name == "Moderate"
        assert get_category(200).name == "Moderate"

    def test_poor(self):
        assert get_category(201).name == "Poor"
        assert get_category(300).name == "Poor"

    def test_very_poor(self):
        assert get_category(301).name == "Very Poor"
        assert get_category(400).name == "Very Poor"

    def test_severe(self):
        assert get_category(401).name == "Severe"
        assert get_category(500).name == "Severe"

    def test_over_500_clamps_to_severe(self):
        assert get_category(999).name == "Severe"

    def test_correct_colors(self):
        assert get_category(25).color == "#55A84F"   # Good
        assert get_category(75).color == "#A3C853"   # Satisfactory
        assert get_category(150).color == "#FFF833"  # Moderate
        assert get_category(250).color == "#F29C33"  # Poor
        assert get_category(350).color == "#E93F33"  # Very Poor
        assert get_category(450).color == "#AF2D24"  # Severe


# ---------------------------------------------------------------------------
# compute_sub_index
# ---------------------------------------------------------------------------

class TestComputeSubIndex:
    # PM2.5 spot checks
    def test_pm25_good(self):
        si = compute_sub_index("PM2.5", 0)
        assert si == 0

    def test_pm25_mid_good(self):
        si = compute_sub_index("PM2.5", 15)
        # (50-0)/(30-0) * (15-0) + 0 = 25
        assert si == 25

    def test_pm25_satisfactory_lower(self):
        si = compute_sub_index("PM2.5", 31)
        # (100-51)/(60-31) * (31-31) + 51 = 51
        assert si == 51

    def test_pm25_upper_bound_satisfactory(self):
        si = compute_sub_index("PM2.5", 60)
        assert si == 100

    def test_pm25_moderate(self):
        si = compute_sub_index("PM2.5", 61)
        assert 101 <= si <= 200  # type: ignore[operator]

    def test_pm25_severe(self):
        si = compute_sub_index("PM2.5", 380)
        assert si == 500

    # NO2 spot check
    def test_no2_good(self):
        si = compute_sub_index("NO2", 20)
        assert si == 25

    # SO2 spot check
    def test_so2_good(self):
        si = compute_sub_index("SO2", 0)
        assert si == 0

    # CO (mg/m³)
    def test_co_good(self):
        si = compute_sub_index("CO", 0.5)
        assert si is not None
        assert 0 <= si <= 50

    def test_co_moderate_lower(self):
        si = compute_sub_index("CO", 2.1)
        assert si is not None
        assert 101 <= si <= 200

    # O3 spot check
    def test_o3_good(self):
        si = compute_sub_index("O3", 25)
        assert si == 25

    # PM10 spot check
    def test_pm10_poor(self):
        si = compute_sub_index("PM10", 300)
        assert si is not None
        assert 201 <= si <= 300

    # Edge cases
    def test_unknown_pollutant_raises(self):
        with pytest.raises(ValueError, match="Unknown pollutant"):
            compute_sub_index("HCHO", 1.0)

    def test_all_pollutants_accept_zero(self):
        for p in POLLUTANTS:
            si = compute_sub_index(p, 0)
            assert si == 0, f"{p} at zero should give SI=0"

    def test_out_of_range_returns_none(self):
        # PM2.5 max BP is 380; above that returns None
        si = compute_sub_index("PM2.5", 9999)
        assert si is None


# ---------------------------------------------------------------------------
# compute_aqi (composite)
# ---------------------------------------------------------------------------

class TestComputeAqi:
    def _sample_concs(self):
        return {"PM2.5": 78.4, "PM10": 150.0, "NO2": 50.0, "SO2": 30.0, "CO": 5.0, "O3": 80.0}

    def test_returns_tuple_of_three(self):
        aqi, dominant, sub = self.compute()
        assert isinstance(aqi, int)
        assert isinstance(dominant, str)
        assert isinstance(sub, dict)

    def compute(self):
        return compute_aqi(self._sample_concs())

    def test_dominant_is_highest_sub_index(self):
        aqi, dominant, sub = self.compute()
        assert aqi == max(sub.values())
        assert sub[dominant] == aqi

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            compute_aqi({})

    def test_all_none_raises(self):
        # All concentrations above valid ranges
        with pytest.raises(ValueError):
            compute_aqi({"PM2.5": 9999, "PM10": 9999})

    def test_single_pollutant(self):
        aqi, dominant, sub = compute_aqi({"PM2.5": 15})
        assert dominant == "PM2.5"
        assert aqi == 25
        assert sub == {"PM2.5": 25}

    def test_aqi_is_max_sub_index(self):
        # Force PM2.5 to dominate
        aqi, dominant, sub = compute_aqi({"PM2.5": 300, "NO2": 10})
        assert dominant == "PM2.5"
        assert aqi == sub["PM2.5"]
        assert aqi > sub.get("NO2", 0)

    def test_sub_indices_dict_has_all_valid_pollutants(self):
        concs = {"PM2.5": 20, "PM10": 60, "NO2": 30}
        _, _, sub = compute_aqi(concs)
        assert set(sub.keys()) == {"PM2.5", "PM10", "NO2"}


# ---------------------------------------------------------------------------
# compute_all_sub_indices
# ---------------------------------------------------------------------------

class TestComputeAllSubIndices:
    def test_returns_one_result_per_pollutant(self):
        concs = {"PM2.5": 20, "NO2": 30}
        results = compute_all_sub_indices(concs)
        assert len(results) == 2

    def test_category_set_for_valid_si(self):
        results = compute_all_sub_indices({"PM2.5": 20})
        assert results[0].category is not None
        assert results[0].category.name == "Good"

    def test_category_none_for_out_of_range(self):
        results = compute_all_sub_indices({"PM2.5": 9999})
        assert results[0].sub_index is None
        assert results[0].category is None
