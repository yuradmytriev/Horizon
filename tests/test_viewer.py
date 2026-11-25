from src import viewer


def test_summary_path_rejects_traversal_and_other_files(tmp_path, monkeypatch):
    monkeypatch.setattr(viewer, "SUMMARIES", tmp_path)
    (tmp_path / "horizon-2026-11-25-en.md").write_text("# hi")
    (tmp_path / "config.json").write_text("{}")

    assert viewer.summary_path("horizon-2026-11-25-en.md") == tmp_path / "horizon-2026-11-25-en.md"
    assert viewer.summary_path("config.json") is None
    assert viewer.summary_path("../config.json") is None
    assert viewer.summary_path("horizon-2026-11-26-en.md") is None
