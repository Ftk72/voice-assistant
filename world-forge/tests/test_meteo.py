from datetime import date

from app.world.meteo import describe_code, parse_forecast

PAYLOAD = {
    "daily": {
        "time": ["2026-07-02", "2026-07-03"],
        "weather_code": [0, 61],
        "temperature_2m_min": [12.3, 14.1],
        "temperature_2m_max": [24.8, 19.0],
        "precipitation_probability_max": [5, 80],
    }
}


def test_parse_forecast_traduit_la_reponse_open_meteo():
    report = parse_forecast(PAYLOAD, place="Lyon")

    assert report.place == "Lyon"
    assert len(report.days) == 2
    assert report.days[0].day == date(2026, 7, 2)
    assert report.days[0].description == "ciel dégagé"
    assert report.days[1].description == "pluie faible"
    assert report.days[1].precipitation_probability == 80


def test_parse_forecast_sans_probabilites():
    payload = {"daily": {**PAYLOAD["daily"]}}
    payload["daily"].pop("precipitation_probability_max")

    report = parse_forecast(payload, place="Lyon")

    assert report.days[0].precipitation_probability is None


def test_code_inconnu_reste_prononcable():
    assert describe_code(42) == "conditions indéterminées"
