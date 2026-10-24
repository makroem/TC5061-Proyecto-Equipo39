"""Contratos de perfiles P3 y evaluación sin información de periodos reservados."""
import numpy as np
import pandas as pd
import pytest

from mibici_equipo39.features import chronological_split, station_usage_profiles
from mibici_equipo39.modeling.p3 import P3Experiment, cluster_metrics


def test_profile_weights_hours_equally_and_excludes_coordinates():
    frame = pd.DataFrame({"station_id": ['1'] * 4,
                          "prediction_time": pd.to_datetime(['2026-01-05 08:00','2026-01-05 09:00',
                                                              '2026-01-06 08:00','2026-01-06 09:00']),
                          "departures": [4,0,0,4], "latitude": [20.0]*4,
                          "sample_weight": [1,1,0,0]})
    plain = station_usage_profiles(frame, ['1'])
    weighted = station_usage_profiles(frame, ['1'], weight='sample_weight')
    assert plain.shape == (1,48)
    assert plain.loc['1','weekday_hour_08'] == .5
    assert plain.loc['1','weekday_hour_09'] == .5
    assert weighted.loc['1','weekday_hour_08'] == 1
    assert weighted.loc['1','weekday_hour_09'] == 0
    assert not any('latitude' in c for c in plain.columns)
    assert np.isfinite(plain.to_numpy()).all()


def synthetic_tables():
    rows=[]
    for split,date in [('train','2026-01-05'),('validation','2026-06-01'),('test','2026-08-03')]:
        for station in range(12):
            for hour in range(24):
                demand=200 if hour == 7+(station % 3)*5 else (station % 4 + 1)
                rows.append((str(station),pd.Timestamp(date)+pd.Timedelta(hours=hour),split,demand))
    data=pd.DataFrame(rows,columns=['station_id','prediction_time','split','departures'])
    return data[['station_id','prediction_time','split']], pd.DataFrame(index=data.index), data.departures


def test_future_demands_cannot_change_train_profiles_or_eligible_stations():
    metadata,X,y=synthetic_tables()
    stations=pd.DataFrame({'station_id':[str(i) for i in range(12)]})
    first=P3Experiment(metadata,X,y,stations)
    changed=y.copy(); changed.loc[metadata['split'].ne('train')] += 10000
    second=P3Experiment(metadata,X,changed,stations)
    assert first.station_ids == second.station_ids
    pd.testing.assert_frame_equal(first.profiles['train'],second.profiles['train'])
    assert not first.profiles['test'].equals(second.profiles['test'])


def test_clustering_metrics_do_not_fabricate_silhouette_for_one_group():
    scores=cluster_metrics(np.ones((6,48)), np.zeros(6), 'test')
    assert scores['test_n_clusters'] == 1
    assert 'test_silhouette' not in scores and 'test_davies_bouldin' not in scores


def test_future_values_do_not_fit_scaler_or_clustering_models():
    metadata,X,y=synthetic_tables()
    stations=pd.DataFrame({'station_id':[str(i) for i in range(12)]})
    first=P3Experiment(metadata,X,y,stations).fit()
    future=y.copy(); future.loc[metadata['split'].ne('train')] += 10000
    second=P3Experiment(metadata,X,future,stations).fit()
    np.testing.assert_array_equal(first.scaler.mean_,second.scaler.mean_)
    for role in ['baseline','candidato']:
        np.testing.assert_array_equal(first.labels[role]['train'],second.labels[role]['train'])


def test_split_rejects_future_or_missing_periods():
    with pytest.raises(ValueError,match='rango temporal'):
        chronological_split(pd.DataFrame({'hour':pd.to_datetime(['2027-01-01'])}))
    with pytest.raises(ValueError,match='tres periodos'):
        chronological_split(pd.DataFrame({'hour':pd.to_datetime(['2026-01-01'])}))

def test_p3experiment_reserves_test_until_after_selection():
    metadata, X, y = synthetic_tables()

    stations = pd.DataFrame(
        {
            "station_id": [str(i) for i in range(12)],
        }
    )

    experiment = P3Experiment(
        metadata,
        X,
        y,
        stations,
    ).fit()

    assert experiment.selected in {
        "baseline",
        "candidato",
        "ninguno",
    }

    assert "test" not in experiment.scaled

    for role in ("baseline", "candidato"):
        assert "test" not in experiment.labels[role]

        assert not any(
            key.startswith("test_")
            for key in experiment.metrics[role]
        )

    if experiment.selected != "ninguno":
        selected_before = experiment.selected

        experiment.evaluate_test()

        assert experiment.selected == selected_before
        assert "test" in experiment.scaled

        for role in ("baseline", "candidato"):
            assert "test" in experiment.labels[role]

            assert any(
                key.startswith("test_")
                for key in experiment.metrics[role]
            )
