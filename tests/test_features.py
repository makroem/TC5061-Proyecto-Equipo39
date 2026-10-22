# -*- coding: utf-8 -*-

import pandas as pd
from mibici_equipo39.features import(
    aggregate_hourly)


def test_station_id_type_is_preserved():

    events = pd.DataFrame({
        "station_id": ["1", "1"],
        "timestamp": [
            pd.Timestamp("2026-01-01 08:00"),
            pd.Timestamp("2026-01-01 08:10"),
        ],
        "event": [-1, 1],
    })

    stations = pd.DataFrame({
        "station_id": [1],
    })

    hourly = aggregate_hourly(
        events,
        stations,
    )

    assert hourly["departures"].sum() == 1
    assert hourly["arrivals"].sum() == 1