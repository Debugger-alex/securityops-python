from pathlib import Path

import yaml


def test_api_waits_for_clamav_database_ready_healthcheck() -> None:
    compose_path = Path(__file__).resolve().parents[2] / "docker-compose.yml"
    compose = yaml.safe_load(compose_path.read_text(encoding="utf-8"))
    clamav = compose["services"]["clamav"]
    api = compose["services"]["api"]

    assert api["depends_on"]["clamav"]["condition"] == "service_healthy"
    assert "ports" not in clamav
    assert clamav["healthcheck"]["start_period"] == "30m"
    assert clamav["healthcheck"]["timeout"] == "5s"
    healthcheck = clamav["healthcheck"]["test"]
    assert healthcheck[0] == "CMD-SHELL"
    assert "PING" in healthcheck[1]
    assert "VERSION" in healthcheck[1]
    assert "/[1-9][0-9]*/" in healthcheck[1]
