from ai.dataset import CLASSES, FEATURES, generate_dataset
from camera.panel_monitor import analyze_panel, create_demo_image
from integration import run_demo


def test_dataset_is_seeded_and_complete():
    data = generate_dataset(samples_per_class=3, seed=7)
    assert len(data) == 15 and set(data.condition) == set(CLASSES)
    assert set(FEATURES).issubset(data.columns)


def test_cv_demo_detects_panel():
    assert analyze_panel(create_demo_image())["panel_detected"]


def test_pipeline_produces_display_fields():
    result = run_demo("Normal", seed=7)
    assert result["status"] == "NORMAL" and 0 <= result["confidence"] <= 1
