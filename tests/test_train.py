import pytest

from mibici_equipo39.modeling import train


def test_controller_stops_when_tables_are_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(train, "REQUIRED", [tmp_path / "metadata.parquet"])
    monkeypatch.setattr(train.C, "ROOT", tmp_path)
    with pytest.raises(SystemExit, match="mibici_equipo39.features"):
        train.check_inputs(allow_dirty=True)


def test_controller_covers_three_questions():
    assert train.QUESTIONS == ("P1", "P2", "P3")

def test_p3_controller_evaluates_test_before_log_and_summary(
    tmp_path,
    monkeypatch,
):
    calls = []

    class FakeP3Experiment:
        def __init__(self, *args):
            self.selected = None
            self.metrics = {
                "baseline": {
                    "val_silhouette": 0.10,
                },
                "candidato": {
                    "val_silhouette": 0.20,
                },
            }

        def fit(self):
            calls.append("fit")
            self.selected = "candidato"
            return self

        def evaluate_test(self):
            calls.append("evaluate_test")

            assert self.selected == "candidato"

            self.metrics["baseline"].update(
                {
                    "test_n_clusters": 3,
                    "test_silhouette": 0.08,
                }
            )

            self.metrics["candidato"].update(
                {
                    "test_n_clusters": 3,
                    "test_silhouette": 0.15,
                }
            )

            return self

        def log(self, member):
            calls.append("log")

            assert member == "persona4"

            for role in ("baseline", "candidato"):
                assert any(
                    key.startswith("test_")
                    for key in self.metrics[role]
                )

    monkeypatch.setattr(
        train,
        "P3Experiment",
        FakeP3Experiment,
    )

    monkeypatch.setattr(
        train,
        "load_tables",
        lambda: (object(), object(), object()),
    )

    monkeypatch.setattr(
        train.pd,
        "read_parquet",
        lambda *args, **kwargs: object(),
    )

    monkeypatch.setattr(
        train.C,
        "REPORTS",
        tmp_path,
    )

    results = train.run(
        ("P3",),
        "persona4",
    )

    assert calls == [
        "fit",
        "evaluate_test",
        "log",
    ]

    assert results["P3"]["selected"] == "candidato"

    for role in ("baseline", "candidato"):
        assert any(
            key.startswith("test_")
            for key in results["P3"]["metrics"][role]
        )

    summary_path = (
        tmp_path / "experiment_summary.json"
    )

    assert summary_path.is_file()

    summary = __import__("json").loads(
        summary_path.read_text(encoding="utf-8")
    )

    for role in ("baseline", "candidato"):
        assert any(
            key.startswith("test_")
            for key in summary["P3"]["metrics"][role]
        )