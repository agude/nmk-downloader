import os
import json

data_dir = './data/raw_json'
output_dir = './data/combined_data'

base_json = None

for filename in sorted(os.listdir(data_dir)):
    if filename.endswith('.json'):
        with open(os.path.join(data_dir, filename)) as f:
            data = json.load(f)

        # First file
        if base_json is None:
            base_json = data
            continue

        # Otherwise add docs data
        new_docs = data["response"]["docs"]
        base_json["response"]["docs"] += new_docs

output_path = os.path.join(output_dir, "combined.json")

with open(output_path, 'w') as out:
    json.dump(base_json, out, indent=2, sort_keys=True)
