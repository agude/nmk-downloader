import json
import os
import textwrap


# Template: https://commons.wikimedia.org/wiki/Template:Artwork
TEMPLATE = """
== {{{{int:filedesc}}}} ==

{{{{Artwork
 |artist             = {{{{Creator:Hans Gude}}}}
 |title              = {title}
 |description        = {description}
 |depicted place     = {depicted_place}
 |date               = {date}
 |medium             = {medium}
 |dimensions         = {dimensions}
 |institution        = {{{{Institution:Nasjonalmuseet for kunst, arkitektur og design}}}}
 |accession number   = {accession_number}
 |credit line        = {credit_line}
 |source             = {source}
 |other_fields       = {other_fields}
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
    # if not techniques_json:
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
            output.append(
                f"{{{{Depicted place | {human_name} | latitude={lat} |longitude={long} }}}}"
            )
        elif human_name and not coordinates:
            output.append(f"{{{{Depicted place | {human_name} }}}}")

    return "<br>".join(output)


def get_title_and_description(titles):
    three_to_two_iso_code = {
        "deu": "de",
        "eng": "en",
        "fra": "fr",
        "ger": "de",
        "nob": "nb",
        "nor": "no",
    }

    output_titles = []
    output_description = ""
    primary_title = None
    for language, language_titles in titles.items():
        language_code = three_to_two_iso_code[language]
        for type_of_title, specific_titles in language_titles.items():
            for title in specific_titles:
                # Illustrations for books have double titles, but one is a
                # description that contains "illustration"
                if "illustrasjon" in title.lower():
                    output_description = f"{{{{{language_code}|{title}}}}}"
                    continue

                # Try to set the primary title
                if not primary_title:
                    if type_of_title == "current" and language_code == "no":
                        primary_title = f"{{{{{language_code}|'''''{title}'''''}}}}"
                        continue

                output_titles.append(
                    f"{{{{{language_code}|''{specific_titles[0]}''}}}}"
                )

    if primary_title:
        output_titles = [primary_title] + output_titles

    # Remove exact duplicates, preserving order
    output_titles = list(dict.fromkeys(output_titles))

    return " ".join(output_titles), output_description


def get_sources(
    nasjonalmuseet_link: str, digitalt_museum_link: str, media_index: str
) -> str:
    direct_image_link = f"https://ms01.nasjonalmuseet.no/api/objects/download?filename={media_index}.tif&size=full"

    output = textwrap.dedent(
        f"""
        * [{direct_image_link} Direct Image Link from the National Museum of Art, Architecture and Design]
        * [{nasjonalmuseet_link} Image on the National Museum of Art, Architecture and Design]
        * [{digitalt_museum_link} Image on the Digitalt Museum]
        """
    ).strip("\n")

    return output


def get_accession_number(
    national_museum_norway_artwork_id: str,
    digitalt_museum_id: str,
    nasjonalmuseet_link: str,
    digitalt_museum_link: str,
    uuid: str,
) -> str:
    output = textwrap.dedent(
        f"""
        * [https://www.wikidata.org/wiki/Property:P9121 National Museum Norway artwork ID]: [{nasjonalmuseet_link} {national_museum_norway_artwork_id}]
        * [https://www.wikidata.org/wiki/Property:P7847 DigitaltMuseum ID]: [{digitalt_museum_link} {digitalt_museum_id}]
        * DigitaltMuseum UUID: [https://api.dimu.org/artifact/uuid/{uuid} {uuid}]
        """
    ).strip("\n")

    return output


def get_credit_line(acquistion_notes: str) -> str:
    if acquistion_notes is None:
        return ""
    return f"{{{{no|{acquistion_notes}}}}}"


def get_other_fields(subjects: str) -> str:
    if subjects is None:
        return ""

    subject_str = ""
    for subject in subjects:
        subject = subject.title()
        subject_str += "* " + subject + "\n"
    subject_str.strip("\n")


    output = textwrap.dedent(
        f"""
        {{{{Information field
            |Name=Subjects
            |Value={{{{en|Subjects from the National Museum of Art, Architecture and Design:\n{subject_str}}}}}
        }}}}
        """
    ).strip("\n")

    return output


data_dir = "./data/our_parsed_data/enriched/"

for filename in sorted(os.listdir(data_dir)):
    if filename.endswith(".json"):
        with open(os.path.join(data_dir, filename)) as f:
            data = json.load(f)

        # Set creation_date
        date_json = data.get("creation_date")
        date = ""
        if date_json:
            date = get_date(date_json)

        # Set medium
        techniques_json = data.get("techniques")
        materials_json = data.get("materials")
        medium = get_medium(techniques_json, materials_json)

        # Set size
        measurements_json = data.get("measurements")
        dimensions = get_dimensions(measurements_json)

        # Set location
        locations_json = data.get("locations")
        if locations_json is not None:
            locations_json = locations_json.get("depicted_location")
            depicted_place = get_depicted_place(locations_json)
        else:
            depicted_place = ""

        # Get title
        titles_json = data.get("titles")
        title, description = get_title_and_description(titles_json)

        # Get source
        nasjonalmuseet_link = data["nasjonalmuseet_link"]
        digitalt_museum_link = data["digitalt_museum_link"]
        media_index = data["media_index"]

        source = get_sources(nasjonalmuseet_link, digitalt_museum_link, media_index)

        # Get accession number
        uuid = data["uuid"]
        national_museum_norway_artwork_id = data["national_museum_norway_artwork_id"]
        digitalt_museum_id = data["digitalt_museum_id"]
        accession_number = get_accession_number(
            national_museum_norway_artwork_id,
            digitalt_museum_id,
            nasjonalmuseet_link,
            digitalt_museum_link,
            uuid,
        )
        # print(accession_number)

        # Credit line
        acquistion_notes = data.get("acquistion_notes")
        credit_line = get_credit_line(acquistion_notes)

        # Subjects
        subjects = data.get("subjects")
        other_fields = get_other_fields(subjects)

        # Template
        wiki_template = TEMPLATE.format(
            depicted_place=depicted_place,
            date=date,
            medium=medium,
            dimensions=dimensions,
            title=title,
            description=description,
            source=source,
            accession_number=accession_number,
            credit_line=credit_line,
            other_fields=other_fields,
            photographer="PLACEHOLDER",
        )
        print(wiki_template)
