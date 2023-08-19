# Path -> Wikimedia Object
import json
from datetime import datetime

def parse_dates(date_str: str) -> str:
    truncated_str = date_str.split("-")[0]
    parsed_time = datetime.strptime(truncated_str, "%Y%m%d")
    # We don't have better than day level granularity
    parsed_date = parsed_time.date()
    return str(parsed_date.isoformat())


with open("./data/uuid_enriched_data/uuid_enriched.json", "r") as f:
    json_data = json.load(f)

mapping = {
    ("identifier.id",): "NG.K&H.B.06516-014",
    ("artifact.uuid",): "8F24C0CF-5D35-4916-B979-ECFF8BA19E99",
    ("artifact.uniqueId",): "011042536344",
    ("digitaltmuseum_link",): "https://digitaltmuseum.org/011042536344",
    ("nasjonalmuseet_link",): "https://www.nasjonalmuseet.no/en/collection/object/NG.K_H.B.06516-014",
    ("uuid_json", "createdDate"): "20140221-020126-763833",
    ("uuid_json", "eventWrap", "acquisition"): "Testamentarisk gave fra Hans Gude",
    ("uuid_json", "eventWrap", "descriptiveDating"): "August eller september 1866",
    ("uuid_json", "eventWrap", "production", "timespan", "fromDate",): "18660801-143000-000",
    ("uuid_json", "eventWrap", "production", "timespan", "toDate",): "18660901-143000-000",
    ("artifact.ingress.subjects",): "[ 'Bildende kunst', 'Bygning' ],",
    (
        "uuid_json",
        "measures",
    ): """[
            { "category": "Hovedm\u00e5l", "measure": 195.0, "sort": 1, "type": "Bredde", "unit": "mm"
            }, { "category": "Hovedm\u00e5l", "measure": 113.0, "sort": 2, "type": "H\u00f8yde", "unit": "mm" }
          ]""",
    # URL of image = f"https://ms01.nasjonalmuseet.no/iip/?iiif=/tif/{index}.tif/full/{width},{height}/0/default.jpg"
    ("uuid_json", "media", "pictures", 0, "index"): 79887,
    ("uuid_json", "media", "pictures", 0, "width"): 3000,
    ("uuid_json", "media", "pictures", 0, "height"): 1765,
    (
        "uuid_json",
        "titles",
    ): """ [
            {
              "language": "NOR",
              "status": "anvendt",
              "title": "H\u00f8yfjell i soloppgang"
            },
            {
              "language": "ENG",
              "status": "anvendt",
              "title": "Norwegian Highlands in Sunrise"
            }
          ] """,
    (
        "uuid_json",
        "technique",
        "techniques",
    ): """ [
              {
                "sort": 1,
                "technique": "Blyant"
              }
            ] """,
    (
        "uuid_json",
        "motif",
        "depictedPlaces",
    ): """ [
              {
                "coordinate": "61.03700499999999, 7.586614999999938",
                "fields": [
                  {
                    "name": "Land",
                    "number": 1,
                    "placeType": "country",
                    "sort": 1,
                    "value": "Norge"
                  },
                  {
                    "code": "1422",
                    "name": "Kommune",
                    "number": 2,
                    "placeType": "municipality",
                    "sort": 3,
                    "value": "L\u00e6rdal"
                  }
                ],
                "role": {
                  "code": "70",
                  "name": "Avbildet sted ",
                  "status": "sannsynlig"
                },
                "uuid": "67E28CD2-7D76-4257-92A5-31449FE3AD47"
              }
]""",
}


def unpack(data, paths):
    current_data = data
    for path in paths:
        current_data = current_data[path]

    return current_data


for doc in json_data["response"]["docs"]:
    start = None
    end = None
    for paths in mapping.keys():
        try:
            if paths == ("uuid_json", "eventWrap", "production", "timespan", "fromDate"):
                data = unpack(doc, paths)
                start = parse_dates(data)
            if paths == ("uuid_json", "eventWrap", "production", "timespan", "toDate"):
                data = unpack(doc, paths)
                end = parse_dates(data)
        except KeyError:
            pass

    if start is not None or end is not None:
        if start != end:
            print("Diff",)
        print(start, end)
