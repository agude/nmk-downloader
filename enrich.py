import os
import json

input_file = "./data/combined_data/combined.json"
output_file = "./data/enriched_data/enriched.json"

base_json = None

def digitaltmuseum_link(unique_id: str) -> str:
    return f"https://digitaltmuseum.org/{unique_id}"


def uuid_link(uuid: str) -> str:
    return f"https://api.dimu.org/artifact/uuid/{uuid}"


def nasjolmuseet_link(identifier_id: str) -> str:
    modifier_id = identifier_id.replace("&", "_")
    return f"https://www.nasjonalmuseet.no/en/collection/object/{modifier_id}"


with open(input_file) as f:
    data = json.load(f)

for doc in data["response"]["docs"]:
    unique_id = doc.get("artifact.uniqueId")
    uuid = doc.get("artifact.uuid")
    identifier_id = doc.get("identifier.id")

    doc["digitaltmuseum_link"] = digitaltmuseum_link(unique_id)
    doc["uuid_link"] = uuid_link(uuid)
    doc["nasjonalmuseet_link"] = nasjolmuseet_link(identifier_id)

with open(output_file, 'w') as out:
    json.dump(data, out, indent=2, sort_keys=True)
