import json
import urllib.request

input_file = "./data/enriched_data/enriched.json"
output_file = "./data/uuid_enriched_data/uuid_enriched.json"

with open(input_file) as f:
    data = json.load(f)

for i, doc in enumerate(data["response"]["docs"]):
    uuid_link = doc.get("uuid_link")
    uuid = doc.get("artifact.uuid")

    print(i, uuid)
    with urllib.request.urlopen(uuid_link) as response:
        contents = response.read()

    json_data = json.loads(contents)
    doc["uuid_json"] = json_data

with open(output_file, "w") as out:
    json.dump(data, out, indent=2, sort_keys=True)
