"""Statistics Canada table 20-10-0056-01: the series of the market benchmark.

The benchmark is a province's retail trade without motor vehicle and parts dealers and without
gasoline stations and fuel vendors ("core retail"). The table does not publish that total by
province, so it is computed from three series: total retail sales, unadjusted.
"""

import json
import urllib.request
from datetime import UTC, datetime

PRODUCT_ID = 20100056
TABLE = "20-10-0056-01"
URL = "https://www150.statcan.gc.ca/t1/wds/rest/getDataFromCubePidCoordAndLatestNPeriods"

# Member ids read in the table metadata on 2026-11-04 (scripts/statcan_metadata.py).
PROVINCES = {
    "NL": ("Newfoundland and Labrador", 2),
    "PE": ("Prince Edward Island", 3),
    "NS": ("Nova Scotia", 4),
    "NB": ("New Brunswick", 5),
    "QC": ("Quebec", 6),
    "ON": ("Ontario", 10),
    "MB": ("Manitoba", 13),
    "SK": ("Saskatchewan", 15),
    "AB": ("Alberta", 16),
    "BC": ("British Columbia", 19),
    "YT": ("Yukon", 21),
    "NT": ("Northwest Territories", 22),
    "NU": ("Nunavut", 23),
}
INDUSTRIES = {"retail_trade": 1, "motor_vehicle_and_parts": 2, "gasoline_stations": 22}
TOTAL_RETAIL_SALES = 1
UNADJUSTED = 1
THOUSANDS = 3  # scalar factor code of the table: values are in thousands of dollars


def coordinate(geography: int, industry: int) -> str:
    """One member id per dimension, in the order of the dimensions, padded to ten with zeros."""
    members = [geography, industry, TOTAL_RETAIL_SALES, UNADJUSTED] + [0] * 6
    return ".".join(str(member) for member in members)


def post(body: list) -> list:
    request = urllib.request.Request(
        URL, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def fetch(latest_n: int = 120) -> dict:
    """Download the three series of every province (one request per province)."""
    answers = []
    for _, geography in PROVINCES.values():
        body = [
            {"productId": PRODUCT_ID, "coordinate": coordinate(geography, i), "latestN": latest_n}
            for i in INDUSTRIES.values()
        ]
        answers += post(body)
    snapshot = parse(answers)
    snapshot["downloaded"] = datetime.now(UTC).isoformat(timespec="seconds")
    return snapshot


def parse(answers: list) -> dict:
    """Snapshot: {"series": {province: {industry: {"YYYY-MM": value or None}}}} and its dates."""
    province_of = {geography: code for code, (_, geography) in PROVINCES.items()}
    industry_of = {member: name for name, member in INDUSTRIES.items()}
    series, months, released = {}, [], []
    for answer in answers:
        if answer.get("status") != "SUCCESS":
            raise RuntimeError(f"Statistics Canada refused a request: {answer}")
        data = answer["object"]
        # Read which series this is from the answer itself, never from the order of the answers.
        geography, industry = (int(member) for member in data["coordinate"].split(".")[:2])
        points = {}
        series.setdefault(province_of[geography], {})[industry_of[industry]] = points
        for point in data["vectorDataPoint"]:
            if point["scalarFactorCode"] != THOUSANDS:
                raise RuntimeError(f"Unexpected unit: {point}")
            month = point["refPer"][:7]
            points[month] = point["value"]
            months.append(month)
            released.append(point["releaseTime"])
    return {
        "table": TABLE,
        "unit": "thousands of dollars",
        "released": max(released),
        "published": max(months),
        "series": series,
    }


def core_retail(snapshot: dict, province: str) -> dict:
    """Monthly benchmark of a province: retail trade minus the two excluded industries.

    A month where one of the three values is not published (None) is None, never a zero.
    """
    series = snapshot["series"][province]
    result = {}
    for month, total in series["retail_trade"].items():
        cars = series["motor_vehicle_and_parts"].get(month)
        fuel = series["gasoline_stations"].get(month)
        missing = total is None or cars is None or fuel is None
        result[month] = None if missing else round(total - cars - fuel, 1)
    return result


def extract(snapshot: dict, province: str, since: str) -> dict:
    """The same snapshot with one province, from a month on: a small frozen copy for the tests."""
    series = {
        name: {month: value for month, value in points.items() if month >= since}
        for name, points in snapshot["series"][province].items()
    }
    return {**snapshot, "series": {province: series}}