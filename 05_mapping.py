# Path -> Wikimedia Object
import json
from datetime import datetime
from collections import namedtuple
from os import path

output_manager = namedtuple("OutputManager", ["field_name", "parser"])

def parse_generic_date(date_str: str) -> datetime:
    return datetime.strptime(date_str, "%Y%m%d-%H%M%S-%f")


def parse_art_date(date_str: str) -> str:
    parsed_date = parse_generic_date(date_str).date()
    return str(parsed_date.isoformat())


def parse_digital_date(date_str: str) -> str:
    parsed_date = parse_generic_date(date_str)
    return str(parsed_date.isoformat())


def parse_generic_string(string: str) -> str:
    return string.strip()


def parse_int(integer: int) -> int:
    return integer


def parse_subjects(subjects: list[str]) -> list[str]:
    # "Fine Art"
    subjects.remove("Bildende kunst")

    translation = {
        "arbeidsliv": "working life",
        "bro": "bridge",
        "byggeskikk": "vernacular architecture",
        "bygning": "building",
        "dyr": "animal",
        "elv": "river",
        "eventyr og sagn": "myths and fairy tales",
        "fjell": "moutain",
        "fjord": "fjord",
        "flora": "flora",
        "folklore": "folklore",
        "foss": "waterfall",
        "fritidsliv": "outdoor life",
        "fugl": "bird",
        "illustrasjon": "illustration",
        "isbre": "glacier",
        "kart": "map",
        "kirke": "church",
        "kystlandskap": "coastal landscape",
        "landskap": "landscape",
        "maritimt": "maritime",
        "reiseskisse": "travel sketch",
        "ski": "skiing",
        "skip / båt": "ship / boat",
        "skoglandskap": "woodlands",
        "skogsinteriør": "forest interior",
    }

    subjects = [val.lower().strip() for val in subjects]
    output = [translation.get(key, key) for key in subjects]

    return output


def parse_techniques(technique_list: list[dict[str, str]]) -> dict[str, str]:
    # This should match Wikidata entries: https://commons.wikimedia.org/wiki/Template:Technique/translation_dashboard
    translation = {
        "akvarell": "watercolor",
        "blyant": "pencil",
        "fargelitografi": "lithography",
        "fargestift": "crayon",
        "gouache": "gouache paint",
        "hvitt kritt": "chalk",
        "kull": "charcoal",
        "lavering": "ink wash",
        "olje": "oil",
        "papir": "paper",
        "penn": "pen",
        "pensel": "brush",
        "streketsning": "etching",
    }

    techniques = [row["technique"].lower().strip() for row in technique_list]
    output = [translation.get(key, key) for key in techniques]

    return output


def parse_materials(materials_list: list[dict[str, str]]) -> dict[str, str]:
    # This should match Wikidata entries: https://commons.wikimedia.org/wiki/Template:Technique/translation_dashboard
    translation = {
        "kartong": "cardboard",  # "Akvarell, gouache og penn over blyant på kartong"
        "lerret": "canvas",
        "papir": "paper",
        "papplate": "cardboard",
        "tre": "wood",  # Human readable comment for this is "Olje på treplate"
        "trefiberplate": "fiberboard",
    }

    materials = [row["material"].lower().strip() for row in sorted(materials_list, key=lambda x: x["sort"])]
    output = [translation.get(key, key) for key in materials]

    return output


def parse_measure(measure_list: list[dict[str, str]]) -> dict[str, str]:
    main_object_key = "main_object"
    frame_key = "frame"
    paper_key = "paper"
    etching_key = "etching_plate"
    page_key = "page"
    image_key = "image"

    to_fill_dicts = {
        main_object_key: {},
        frame_key: {},
        paper_key: {},
        etching_key: {},
        page_key: {},
        image_key: {},
    }

    for measure in measure_list:
        object_category = measure["category"]

        # Main artwork
        if object_category == "Hovedmål":
            dict_to_fill = to_fill_dicts[main_object_key]
        # Frame
        elif object_category == "Rammemål":
            dict_to_fill = to_fill_dicts[frame_key]
        # Paper
        elif object_category == "Papir":
            dict_to_fill = to_fill_dicts[paper_key]
        # Etching Plate
        elif object_category == "Platemål":
            dict_to_fill = to_fill_dicts[etching_key]
        # Page in a book
        elif object_category == "Arkets mål":
            dict_to_fill = to_fill_dicts[page_key]
        # Image
        elif object_category == "Bildemål":
            dict_to_fill = to_fill_dicts[image_key]
        else:
            print(f"UNKNOWN: {category=}")
            continue

        # Read values
        dimension = measure["type"]
        dimension_key = None

        if dimension == "Høyde":
            dimension_key = "height"
        elif dimension == "Bredde":
            dimension_key = "width"
        elif dimension == "Dybde":
            dimension_key = "depth"
        else:
            print(f"UNKNOWN: {dimension=}")
            continue

        dict_to_fill[dimension_key] = measure["measure"]
        dict_to_fill[f"{dimension_key}_unit"] = measure["unit"]

    output = { key: val for key, val in to_fill_dicts.items() if val }

    return output


def parse_titles(titles_list: list[str]) -> dict[str, str]:
    status_map = {
        "anvendt": "current",
        "current": "current",
        "original": "original",
    }

    output = {}
    for title_block in titles_list:
        if not title_block:
            continue

        language_code = title_block["language"].lower()
        status_key = title_block.get("status", "current").lower()
        status = status_map[status_key]
        title = title_block["title"].strip()

        if language_code not in output:
            output[language_code] = {}
        if status not in output[language_code]:
            output[language_code][status] = []
        output[language_code][status].append(title)

    return output


def parse_location(locations):
    place_type_map = {
        "adresse": "adress",
        "land": "country",
        "fylke": "county",
        "kommune": "municipality",
        # Used for things like "Mountain range"
        "område": "area",
        "områdepres": "specific_area",
    }

    role_type_map = {
        "avbildet sted": "depicted_location",
        "produksjonssted": "produced_at",
    }

    location_map = {
        "Danmark": "Denmark",
        "Frankrike": "France",
        "Norge": "Norway",
        "Skottland": "Scotland",
        "Storbritannia": "Great Britain",
        "Sveits": "Switzerland",
        "Sverige": "Sweden",
        "Tyskland": "Germany",
        "Østerrike": "Austria",
        # Sub-country level
        "Lindesnes fyr": "Lindesnes Lighthouse",
        "Oscarsborg festning": "Oscarsborg fortress",
        "Rheinland-Pfalz": "Rhineland-Palatinate",
        "Schloss Hohenaschau": "Hohenaschau Castle",
        "Schloss Altenklingen": "Altenklingen Castle",
        "St.-Katharinen-Kirche": "Saint Catherine of Alexandria Church",
        # Typos, etc.
        "6859 Sogndal": "Slinde",
        "Aschau am Chiemgau": "Aschau im Chiemgau",
    }

    output = {}
    for location in locations:
        location_output = {}

        coordinates = location.get("coordinate")

        role = location["role"]
        role_type = role["name"].strip().lower()
        role_type = role_type_map[role_type]
        role_status = role.get("status")

        if role_type not in output:
            output[role_type] = []

        if coordinates:
            location_output["coordinates"] = coordinates
        if role_status:
            location_output["place_accuracy"] = role_status

        fields = sorted(location["fields"], key=lambda x: x["sort"])
        location_output["place_names"] = []
        for field in fields:
            name = field["name"].lower()
            name = place_type_map.get(name, name)
            number = field["number"]
            value = field["value"].strip()
            value = location_map.get(value, value)

            location_output["place_names"].append({
                "name": value,
                "level": number,
                "place_type": name,
            })

        # Also lets construct a "Human readable name"
        human_name = ", ".join(f["name"] for f in reversed(location_output["place_names"]))
        location_output["human_name"] = human_name

        output[role_type].append(location_output)

    return output


def unpack(data, paths):
    """Extract data from a JSON blob by following the whole path.

    Returns None if the path does not exist.
    """
    current_data = data
    for path in paths:
        try:
            current_data = current_data[path]
        except KeyError:
            return None

    return current_data


with open("./data/uuid_enriched_data/uuid_enriched.json", "r") as f:
    json_data = json.load(f)

mapping = {
    ("identifier.id",): output_manager("national_museum_norway_artwork_id", parse_generic_string),
    ("artifact.uuid",): output_manager("uuid", parse_generic_string),
    ("artifact.uniqueId",): output_manager("digitalt_museum_id", parse_generic_string),
    ("digitaltmuseum_link",): output_manager("digitalt_museum_link", parse_generic_string),
    ("nasjonalmuseet_link",): output_manager("nasjonalmuseet_link", parse_generic_string),
    ("uuid_json", "createdDate"): output_manager("digital_item_created_at", parse_digital_date),
    ("uuid_json", "eventWrap", "acquisition"): output_manager("acquistion_notes", parse_generic_string),
    ("uuid_json", "eventWrap", "descriptiveDating"): output_manager("descriptive_date", parse_generic_string),
    ("uuid_json", "eventWrap", "production", "timespan", "fromDate",): output_manager("from_date", parse_art_date),
    ("uuid_json", "eventWrap", "production", "timespan", "toDate",): output_manager("to_date", parse_art_date),
    ("artifact.ingress.subjects",): output_manager("subjects", parse_subjects),
    ("uuid_json", "measures",): output_manager("measurements", parse_measure),
    ("uuid_json", "media", "pictures", 0, "index"): output_manager("media_index" , parse_int),
    ("uuid_json", "media", "pictures", 0, "width"): output_manager("media_width_pixels" , parse_int),
    ("uuid_json", "media", "pictures", 0, "height"): output_manager("media_height_pixels" , parse_int),
    ("uuid_json", "titles",): output_manager("titles", parse_titles),
    ("uuid_json", "technique", "techniques",): output_manager("techniques", parse_techniques),
    ("uuid_json", "material", "comment",): output_manager("material_comment", parse_generic_string),
    ("uuid_json", "material", "materials",): output_manager("materials", parse_materials),
    ("uuid_json", "motif", "depictedPlaces",): output_manager("locations", parse_location),
}

output_dir = "./data/our_parsed_data/raw/"

for doc in json_data["response"]["docs"]:
    doc_data = {}
    for paths, output_tuple in mapping.items():
        data = unpack(doc, paths)
        if data is None:
            continue
        doc_data[output_tuple.field_name] = output_tuple.parser(data)

    output_file = path.join(output_dir, f"{doc_data['uuid']}.json")

    with open(output_file, "w") as f:
        f.write(json.dumps(doc_data, sort_keys=True, indent=2))
