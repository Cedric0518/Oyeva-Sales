"""Print the dimensions of Statistics Canada table 20-10-0056-01 (retail trade, monthly).

Run once to find the member ids (province, industry, adjustment) the market comparison needs.
"""

import json
import urllib.request

PRODUCT_ID = 20100056
URL = "https://www150.statcan.gc.ca/t1/wds/rest/getCubeMetadata"


def post(url: str, body: list) -> list:
    request = urllib.request.Request(
        url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def main() -> None:
    cube = post(URL, [{"productId": PRODUCT_ID}])[0]["object"]
    print(cube["cubeTitleEn"])
    print("Data from", cube["cubeStartDate"], "to", cube["cubeEndDate"])
    print("Released", cube["releaseTime"])
    for dimension in cube["dimension"]:
        members = dimension["member"]
        print(f"\n{dimension['dimensionPositionId']}. {dimension['dimensionNameEn']}")
        for member in members:
            # Geography also lists cities: keep Canada and the provinces only.
            if dimension["dimensionPositionId"] == 1 and member["parentMemberId"] not in (None, 1):
                continue
            print(f"  {member['memberId']:>4}  {member['memberNameEn']}")


if __name__ == "__main__":
    main()
