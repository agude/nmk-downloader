from datetime import datetime
import json
import os


# Template: https://commons.wikimedia.org/wiki/Template:Artwork
"""
== {{int:filedesc}} ==

{{Artwork
 |artist             = {{Creator:Hans Gude}}
 |title              =
 |description        =
 |depicted people    =
 |depicted place     =
 |date               =
 |medium             =
 |dimensions         =
 |institution        = {{Institution:Nasjonalmuseet for kunst, arkitektur og design}}
 |department         =
 |accession number   =
 |place of creation  =
 |place of discovery =
 |object history     =
 |exhibition history =
 |credit line        =
 |inscriptions       =
 |notes              =
 |references         =
 |source             =
 |permission         =
 |other_versions     =
 |wikidata           =
}}

=={{int:license-header}}==

{{Licensed-PD-Art|PD-old-auto-expired|cc-by-4.0|attribution=Nasjonalmuseet/|deathyear=1903}}

[[Category:Drawings by Hans Gude in the Nasjonalmuseet for kunst, arkitektur og design]]
"""


def get_date(creation_date_json) -> str:
    # If date is exact, it's easy
    if not creation_date_json["range_of_dates"]:
        return creation_date_json["created_at_date"]

    # Otherwise, it's a range, and needs the other date template
    # https://commons.wikimedia.org/wiki/Template:Other_date
    start_date = creation_date_json["created_at_date_start"]
    end_date = creation_date_json["created_at_date_end"]

    # Sometimes we just don't know the date, in which case the museum uses a
    # very large range ending at Gude's death year
    if end_date == "1903" and start_date in ("1838", "1840"):
        return f"{{{{Other_date|?|{start_date}|{end_date}}}}}"

    # Ranges
    else:
        return f"{{{{Other_date|between|{start_date}|{end_date}}}}}"


data_dir = "./data/our_parsed_data/enriched/"

for filename in sorted(os.listdir(data_dir)):
    if filename.endswith(".json"):
        with open(os.path.join(data_dir, filename)) as f:
            data = json.load(f)

        uuid = data["uuid"]
        print()
        print(uuid)

        # Set creation_date
        date_json = data.get("creation_date")
        date = ""
        if date_json:
            date = get_date(date_json)
        print(date)

