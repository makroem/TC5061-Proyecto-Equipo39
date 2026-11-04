from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from mibici_equipo39.serving.verify_model import check_station_sample, make_inputs


def test_basic_profile_preserves_the_original_cases():
    rows, types, frame = make_inputs("basic")
    assert len(rows) == 72
    assert set(frame["station_id"]) == {"10", "20", "99999"}
    assert set(frame["month"]) == {6}
    assert set(frame["day_of_week"]) == {5}
    assert frame.dtypes.astype(str).to_dict() == types


def test_extended_profile_covers_months_days_hours_without_duplicate_inputs():
    rows, types, frame = make_inputs("extended")
    assert len(rows) == 12096
    assert set(frame["month"]) == set(range(1, 13))
    assert set(frame["day_of_week"]) == set(range(7))
    assert set(frame["hour_of_day"]) == set(range(24))
    assert not frame.duplicated(["station_id", "month", "day_of_week", "hour_of_day"]).any()
    assert frame.groupby("station_id").size().eq(2016).all()
    assert frame.loc[frame["day_of_week"] < 5, "is_weekend"].eq(0).all()
    assert frame.loc[frame["day_of_week"] >= 5, "is_weekend"].eq(1).all()
    assert frame.dtypes.astype(str).to_dict() == types
    assert np.isfinite(frame.select_dtypes(include="number")).all().all()


def test_unrecognized_profile_is_rejected():
    with pytest.raises(ValueError, match="Perfil"):
        make_inputs("other")


def baseline(stations):
    index = pd.MultiIndex.from_product([stations, [0], [0]],
                                      names=["station_id", "day_of_week", "hour_of_day"])
    return SimpleNamespace(means_=[pd.Series(1.0, index=index)])


def test_station_membership_is_checked_against_the_fitted_baseline():
    sample = check_station_sample(baseline(["10", "20", "30"]), ["10", "20", "99999"])
    assert sample == {"known_station_ids": ["10", "20"],
                      "unknown_station_ids": ["99999"], "known_stations_in_model": 3}


@pytest.mark.parametrize("known", [["10"], ["10", "20", "99999"]])
def test_wrong_station_categories_are_rejected(known):
    with pytest.raises(ValueError, match="estaciones"):
        check_station_sample(baseline(known), ["10", "20", "99999"])


def test_a_different_model_cannot_claim_the_same_station_coverage():
    with pytest.raises(ValueError, match="baseline"):
        check_station_sample(SimpleNamespace(), ["10", "99999"])
