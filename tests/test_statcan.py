import pytest

from api.market.statcan import coordinate, core_retail, extract, parse

SNAPSHOT = {
    "published": "2026-02",
    "series": {
        "ON": {
            "retail_trade": {"2026-01": 1000.0, "2026-02": 900.0},
            "motor_vehicle_and_parts": {"2026-01": 250.0, "2026-02": 200.0},
            "gasoline_stations": {"2026-01": 100.0, "2026-02": None},
        }
    },
}


def point(month: str, value: float | None) -> dict:
    return {"refPer": f"{month}-01", "value": value, "scalarFactorCode": 3, "releaseTime": "T"}


def answer(coord: str, *points: dict) -> dict:
    return {"status": "SUCCESS", "object": {"coordinate": coord, "vectorDataPoint": list(points)}}


def test_coordinate_has_one_member_per_dimension():
    assert coordinate(10, 22) == "10.22.1.1.0.0.0.0.0.0"


def test_core_retail_removes_cars_and_fuel_and_keeps_gaps():
    assert core_retail(SNAPSHOT, "ON") == {"2026-01": 650.0, "2026-02": None}


def test_extract_keeps_one_province_from_a_month_on():
    small = extract(SNAPSHOT, "ON", "2026-02")
    assert small["series"]["ON"]["retail_trade"] == {"2026-02": 900.0}
    assert small["published"] == "2026-02"


def test_parse_reads_each_series_from_its_coordinate():
    snapshot = parse(
        [
            answer("10.22.1.1.0.0.0.0.0.0", point("2026-08", 5.0)),
            answer("10.1.1.1.0.0.0.0.0.0", point("2026-07", 9.0), point("2026-08", 10.0)),
        ]
    )
    assert snapshot["series"]["ON"]["gasoline_stations"] == {"2026-08": 5.0}
    assert snapshot["series"]["ON"]["retail_trade"] == {"2026-07": 9.0, "2026-08": 10.0}
    assert snapshot["published"] == "2026-08"


def test_parse_stops_on_a_refused_request():
    with pytest.raises(RuntimeError):
        parse([{"status": "FAILED", "object": "Invalid coordinate"}])
