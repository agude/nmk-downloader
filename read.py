import json

with open("./data/combined_data/combined.json") as f:
    json_data = json.load(f)

print(len(json_data["response"]["docs"]))
