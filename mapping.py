# Path -> Wikimedia Object
import json
from datetime import datetime
from collections import namedtuple

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

    return subjects


def parse_measure(measure_list: list[dict[str, str]]) -> dict[str, str]:
    # keys
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
    ( "uuid_json", "measures",): output_manager("measurements", parse_measure),
    # URL of image = f"https://ms01.nasjonalmuseet.no/iip/?iiif=/tif/{index}.tif/full/{width},{height}/0/default.jpg"
    ("uuid_json", "media", "pictures", 0, "index"):  output_manager("media_index" , parse_int),
    ("uuid_json", "media", "pictures", 0, "width"):  output_manager("media_width_pixels" , parse_int),
    ("uuid_json", "media", "pictures", 0, "height"): output_manager("media_height_pixels" , parse_int),
    ( "uuid_json", "titles",): """ [
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
    ( "uuid_json", "technique", "techniques",): """ [
              {
                "sort": 1,
                "technique": "Blyant"
              }
            ] """,
    ( "uuid_json", "motif", "depictedPlaces",): """ [
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



for doc in json_data["response"]["docs"]:
    doc_data = {}
    for paths, output_tuple in mapping.items():
        if isinstance(output_tuple, output_manager):
            data = unpack(doc, paths)
            if data is None:
                continue
            doc_data[output_tuple.field_name] = output_tuple.parser(data)
    if len(doc_data["measurements"]) > 1:
        print(json.dumps(doc_data, sort_keys=True, indent=2))
