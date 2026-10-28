"""Casos límite que no cubría la revisión inicial de P1/P2."""
import subprocess

import numpy as np
import pandas as pd
import pytest

from mibici_equipo39.features import CALENDAR_FEATURES
from mibici_equipo39.modeling import tracking
from mibici_equipo39.modeling.p2 import P2Experiment


@pytest.mark.parametrize('label', [0, 1])
def test_p2_can_evaluate_a_single_training_class(label):
    metadata = pd.DataFrame({
        'station_id': ['1'] * 9,
        'prediction_time': pd.date_range('2026-01-01', periods=9, freq='h'),
        'split': ['train'] * 3 + ['validation'] * 3 + ['test'] * 3,
    })
    X = pd.DataFrame({name: np.zeros(9) for name in CALENDAR_FEATURES})
    targets = pd.DataFrame({'capacity': [20] * 9, 'flow_min': [0] * 9,
                            'flow_max': [0] * 9, 'y_bikes': [label] * 9,
                            'y_docks': [label] * 9})
    experiment = P2Experiment(metadata, X, targets).fit()
    for kind in ['baseline', 'candidato']:
        for risk in ['bikes', 'docks']:
            np.testing.assert_array_equal(experiment.scores[kind][risk], np.full(9, label))
            assert experiment.actual_models[kind][risk] == 'DummyClassifier'


@pytest.mark.parametrize('failed_command', ['rev-parse', 'status'])
def test_git_failure_cannot_be_reported_as_clean(monkeypatch, failed_command):
    def git_result(args, **kwargs):
        if args[1] == failed_command:
            return subprocess.CompletedProcess(args, 128, stdout='', stderr='Git failed')
        return subprocess.CompletedProcess(args, 0, stdout='a' * 40 + '\n', stderr='')
    monkeypatch.setattr(tracking.subprocess, 'run', git_result)
    with pytest.raises(RuntimeError, match='Git'):
        tracking.git_state()


@pytest.mark.integration
def test_new_untracked_code_is_dirty(tmp_path, monkeypatch):
    def git(*args):
        subprocess.run(['git', *args], cwd=tmp_path, check=True, capture_output=True)
    git('init')
    (tmp_path / 'tracked.py').write_text('value = 1\n', encoding='utf-8')
    git('add', 'tracked.py')
    git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-m', 'initial')
    monkeypatch.setattr(tracking.C, 'ROOT', tmp_path)
    assert tracking.git_state()[1] is False
    (tmp_path / 'new_module.py').write_text('value = 2\n', encoding='utf-8')
    assert tracking.git_state()[1] is True
