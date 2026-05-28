def get_severity(weak_point: str) -> str:
    """Get severity level for a weak point."""
    text = weak_point.lower()
    if any(w in text for w in [
        'sql injection', 'injection', 'password exposed',
        'credential', 'overflow', 'authentication'
    ]):
        return "CRITICAL"
    elif any(w in text for w in [
        'division by zero', 'crash', 'null', 'none type',
        'unhandled exception', 'unsafe'
    ]):
        return "HIGH"
    elif any(w in text for w in [
        'file not closed', 'resource leak', 'type error',
        'index', 'key error', 'boundary'
    ]):
        return "MEDIUM"
    else:
        return "LOW"


def get_severity_color(severity: str) -> str:
    """Get color for severity badge."""
    colors = {
        "CRITICAL": "#ff0000",
        "HIGH": "#ff3b3b",
        "MEDIUM": "#ffd700",
        "LOW": "#00ff88"
    }
    return colors.get(severity, "#a0a0b0")


def calculate_score(
    weak_points: list,
    bugs_found: int,
    total_tests: int
) -> dict:
    """Calculate overall security score."""
    score = 100

    for wp in weak_points:
        severity = get_severity(wp)
        deductions = {
            "CRITICAL": 15,
            "HIGH": 10,
            "MEDIUM": 5,
            "LOW": 2
        }
        score -= deductions.get(severity, 2)

    score -= bugs_found * 8
    score = max(0, min(100, score))

    if score >= 80:
        label = "SECURE"
        color = "#00ff88"
    elif score >= 60:
        label = "MODERATE RISK"
        color = "#ffd700"
    elif score >= 40:
        label = "VULNERABLE"
        color = "#ff8c00"
    else:
        label = "CRITICAL RISK"
        color = "#ff0000"

    return {
        "score": score,
        "label": label,
        "color": color,
        "critical": sum(1 for wp in weak_points
                       if get_severity(wp) == "CRITICAL"),
        "high": sum(1 for wp in weak_points
                   if get_severity(wp) == "HIGH"),
        "medium": sum(1 for wp in weak_points
                     if get_severity(wp) == "MEDIUM"),
        "low": sum(1 for wp in weak_points
                  if get_severity(wp) == "LOW"),
    }
