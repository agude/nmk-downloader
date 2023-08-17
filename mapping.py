# Path -> Wikimedia Object
import json

with open("./data/uuid_enriched_data/uuid_enriched.json", "r") as f:
    json_data = json.load(f)

mapping = {
    ("identifier.id",): "NG.K&H.B.06516-014",
    ("artifact.uuid",): "8F24C0CF-5D35-4916-B979-ECFF8BA19E99",
    ("artifact.ingress.title",): "Hus ved veien [Tegning]",
    ("artifact.uniqueId",): "011042536344",
    ("digitaltmuseum_link",): "https://digitaltmuseum.org/011042536344",
    ("nasjonalmuseet_link",): "https://www.nasjonalmuseet.no/en/collection/object/NG.K_H.B.06516-014",
    ("uuid_json", "createdDate"): "20140221-020126-763833",
    ("uuid_json", "eventWrap", "acquisition"): "Testamentarisk gave fra Hans Gude",
    ("uuid_json", "eventWrap", "events", 0, "timespan", "fromDate"): "18660801-143000-000",
    ("uuid_json", "eventWrap", "events", 0, "timespan", "toDate"): "18660901-143000-000",
}

def unpack(data, paths):
    current_data = data
    for path in paths:
        current_data = current_data[path]

    return current_data


for doc in json_data["response"]["docs"]:
    for paths in mapping.keys():
        print(paths, unpack(doc, paths))
    break
