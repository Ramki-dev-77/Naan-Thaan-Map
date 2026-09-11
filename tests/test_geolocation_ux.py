"""
Campus Navigation System — Geolocation UX & Accuracy Classification Tests
"""

def classify_accuracy_py(accuracy_meters: float):
    """Mirror of client-side classification logic for test verification."""
    if accuracy_meters <= 10:
        return "excellent"
    elif accuracy_meters <= 25:
        return "good"
    elif accuracy_meters <= 50:
        return "usable"
    elif accuracy_meters <= 100:
        return "approximate"
    else:
        return "poor"


def test_accuracy_tier_boundaries():
    """Verify accuracy classification rules."""
    assert classify_accuracy_py(5) == "excellent"
    assert classify_accuracy_py(10) == "excellent"
    assert classify_accuracy_py(10.1) == "good"
    assert classify_accuracy_py(25) == "good"
    assert classify_accuracy_py(35) == "usable"
    assert classify_accuracy_py(50) == "usable"
    assert classify_accuracy_py(75) == "approximate"
    assert classify_accuracy_py(100) == "approximate"
    assert classify_accuracy_py(105) == "poor"
    assert classify_accuracy_py(500) == "poor"
