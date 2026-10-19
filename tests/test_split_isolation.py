"""Regresiones de aislamiento entre conjuntos y conservación del manifiesto."""
import json

import numpy as np
import pandas as pd
import pytest

from mibici_equipo39 import features as F


def hourly_grid():
    hours = pd.date_range('2025-10-01', '2026-10-01', freq='h', inclusive='left')
    return pd.DataFrame({
        'station_id': pd.array(['1'] * len(hours), dtype='string'),
        'hour': hours, 'departures': np.arange(len(hours)) % 11,
        'arrivals': np.arange(len(hours)) % 7,
    })


def split(frame):
    frame = F.add_calendar_features(frame)
    frame = frame.loc[frame.hour.ge('2025-10-09')].reset_index(drop=True)
    return F.random_grouped_split(frame, data_version='synthetic-audit')


def test_reserved_departures_cannot_change_training_predictors():
    original = hourly_grid()
    base, manifest = split(original)
    reserved = set(manifest['days']['validation'] + manifest['days']['test'])
    modified = original.copy()
    modified.loc[modified.hour.dt.strftime('%Y-%m-%d').isin(reserved), 'departures'] += 1000
    changed, _ = split(modified)
    before = F.build_supervised_tables(base)
    after = F.build_supervised_tables(changed)
    train = base['split'].eq('train')
    pd.testing.assert_frame_equal(before['X'].loc[train], after['X'].loc[train])
    assert F.FEATURE_COLUMNS == F.CALENDAR_FEATURES
    assert list(before['X']) == F.CALENDAR_FEATURES
    assert not {'departures', 'arrivals', 'capacity', 'flow_min', 'flow_max', 'y_bikes', 'y_docks'} & set(before['X'])


def test_confirmed_split_is_reproduced_without_rewriting(tmp_path):
    frame, manifest = split(hourly_grid())
    path = tmp_path / 'split_manifest.json'
    text = json.dumps(manifest, indent=4) + '\n'
    path.write_text(text, encoding='utf-8')
    _, reproduced = F.random_grouped_split(frame, data_version='synthetic-audit', manifest_path=path)
    assert reproduced == manifest
    assert path.read_text(encoding='utf-8') == text


@pytest.mark.parametrize('field,value', [
    ('split_id', 'incorrect'), ('seed', 123), ('data_version', 'other-data'),
    ('strategy', 'other-strategy'), ('days', {'train': [], 'validation': [], 'test': []}),
])
def test_mismatching_manifest_is_rejected_and_preserved(tmp_path, field, value):
    frame, manifest = split(hourly_grid())
    manifest[field] = value
    path = tmp_path / 'split_manifest.json'
    text = json.dumps(manifest)
    path.write_text(text, encoding='utf-8')
    with pytest.raises(ValueError, match='no coincide'):
        F.random_grouped_split(frame, data_version='synthetic-audit', manifest_path=path)
    assert path.read_text(encoding='utf-8') == text


def test_missing_confirmed_manifest_does_not_create_one(tmp_path):
    frame, _ = split(hourly_grid())
    path = tmp_path / 'split_manifest.json'
    with pytest.raises(FileNotFoundError, match='PR explícito'):
        F.random_grouped_split(frame, data_version='synthetic-audit', manifest_path=path)
    assert not path.exists()
