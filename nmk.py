import requests
import json
from os.path import join


def make_request(start: int):
    base_url = "https://api.dimu.org/api/solr/select?"

    payload = {
        "q": "*",
        "wt": "json",
        "api.key": "demo",
        "start": start,
        "fq": [
            "identifier.owner:NMK*",
            "artifact.producer:Hans Gude",
        ],
        "rows": 10,
    }
    response = requests.post(url=base_url, params=payload)

    return response


output_dir = "./data/raw_json/"
TOTAL_N = 1018


for i, start in enumerate(range(0, TOTAL_N, 10)):
    output_file = join(output_dir, f"{i:03}.json")
    print(i, output_file)

    response = make_request(start)
    print(response)
    response_json = response.json()

    with open(output_file, "w") as f:
        print(f"Writing  {output_file}")
        json.dump(response_json, f, indent=2)
