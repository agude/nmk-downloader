from datetime import datetime
import json
import os


# Template: https://commons.wikimedia.org/wiki/Template:Artwork
TEMPLATE  = """
== {{{{int:filedesc}}}} ==

{{{{Artwork
 |artist             = {{{{Creator:Hans Gude}}}}
 |title              = {title}
 |description        =
 |depicted people    =
 |depicted place     = {depicted_place}
 |date               = {date}
 |medium             = {medium}
 |dimensions         = {dimensions}
 |institution        = {{{{Institution:Nasjonalmuseet for kunst, arkitektur og design}}}}
 |department         =
 |accession number   =
 |place of creation  =
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
}}}}

=={{{{int:license-header}}}}==

{{{{Licensed-PD-Art|PD-old-auto-expired|cc-by-4.0|attribution=Nasjonalmuseet/{photographer}|deathyear=1903}}}}

[[Category:Drawings by Hans Gude in the Nasjonalmuseet for kunst, arkitektur og design]]
[[Category:Images from Digitalt Museum, Norway]]
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


def get_medium(techniques_json, materials_json) -> str:
    # Uses the technique template
    # https://commons.wikimedia.org/wiki/Template:Technique

    final_list = ["{{Technique"]

    technique_starts = [
        " | ",
        " | and=",
        " | and2=",
        " | and3=",
        " | and4=",
    ]

    if techniques_json:
        final_list += [s + t for s, t in zip(technique_starts, techniques_json)]
    #if not techniques_json:
    #    print("AHHHHHHHHHH")

    materials_starts = [
        " | on=",
        " | mounted=",
    ]

    if materials_json:
        final_list += [s + m for s, m in zip(materials_starts, materials_json)]

    final_list += ["}}"]

    return "".join(final_list)


def get_dimensions(measurements) -> str:
    # The main art
    main_object = measurements["main_object"]
    height = main_object["height"]
    width = main_object["width"]
    height_unit = main_object["height_unit"]
    width_unit = main_object["width_unit"]

    if width_unit != height_unit:
        raise ValueError("Units don't match")

    main_size_template = f"{{{{Size|unit={width_unit}|height={height}|width={width}}}}}"

    # Frame, if exists
    frame = measurements.get("frame")
    if frame is not None:
        frame_height = frame["height"]
        frame_width = frame["width"]
        frame_height_unit = frame["height_unit"]
        frame_width_unit = frame["width_unit"]
        frame_depth = frame["depth"]

        if frame_height_unit != frame_width_unit:
            raise ValueError("Frame size units don't match")

        frame_size_template = f"{{{{Size|unit={frame_width_unit}|height={frame_height}|width={frame_width}|depth={frame_depth}}}}}"

        return f"{main_size_template}<br>{{{{With frame}}}}: {frame_size_template}"

    return main_size_template


def get_depicted_place(depicted_locations):
    # Sometimes we don't have locations
    if depicted_locations is None:
        return None

    output = []
    for location in depicted_locations:
        coordinates = location.get("coordinates")
        human_name = location.get("human_name")
        if coordinates:
            lat, long = coordinates.split(", ")
            # 5 digits is meter accuracy, which is far higher than these coordinates are
            lat = round(float(lat), 5)
            long = round(float(long), 5)

        if human_name and coordinates:
            output.append(f"{{{{Depicted place | {human_name} | latitude={lat} |longitude={long} }}}}")
        elif human_name and not coordinates:
            output.append(f"{{{{Depicted place | {human_name} }}}}")

    return "<br>".join(output)


def get_title(titles):
    three_to_two_iso_code = {
        "deu": "de",
        "eng": "en",
        "fra": "fr",
        "ger": "de",
        "nob": "nb",
        "nor": "no",
    }
    for language in titles:
        code = three_to_two_iso_code[language]
        print(code, titles[language])


data_dir = "./data/our_parsed_data/enriched/"

for filename in sorted(os.listdir(data_dir)):
    if filename.endswith(".json"):
        with open(os.path.join(data_dir, filename)) as f:
            data = json.load(f)

        uuid = data["uuid"]
        #print()
        #print(uuid)

        # Set creation_date
        date_json = data.get("creation_date")
        date = ""
        if date_json:
            date = get_date(date_json)
        #print(date)

        # Set medium
        techniques_json = data.get("techniques")
        materials_json = data.get("materials")
        medium = get_medium(techniques_json, materials_json)
        #print(medium)

        # Set size
        measurements_json = data.get("measurements")
        dimensions = get_dimensions(measurements_json)
        #print(dimensions)

        # Set location
        locations_json = data.get("locations")
        if locations_json is not None:
            locations_json = locations_json.get("depicted_location")
            depicted_place = get_depicted_place(locations_json)
            #print(depicted_place)
        else:
            depicted_place = ""

        # Get title
        titles_json = data.get("titles")
        title = get_title(titles_json)

        wiki_template = TEMPLATE.format(
                depicted_place = depicted_place,
                date = date,
                medium = medium,
                dimensions = dimensions,
                title = title,
                photographer = "PLACEHOLDER",
            )
        #print(wiki_template)
