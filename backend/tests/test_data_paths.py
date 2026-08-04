from app.data_paths import get_data_dir


def test_get_data_dir_points_at_catalog_fixtures():
    data = get_data_dir()
    assert (data / "catalog-fixtures.json").exists()
    assert (data / "ranker-weights.json").exists()
    assert (data / "season-calendar.json").exists()
    assert (data / "replenishment-cycles.json").exists()
