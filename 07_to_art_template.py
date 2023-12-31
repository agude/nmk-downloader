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

{{{{Licensed-PD-Art|PD-old-auto-expired|cc-by-4.0|attribution=Nasjonalmuseet{photographer}|deathyear=1903}}}}

[[Category:Drawings by Hans Gude in the Nasjonalmuseet for kunst, arkitektur og design]]
[[Category:Images from Digitalt Museum, Norway]]

<!-- Raw JSON data used to build this page. -->
{raw_data}
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
    # For the primary title, prefer languages in this order
    language_preference_stack  = (
        "nor",
        "nob",
        "ger",
        "deu",
        "eng",
        "fra",
    )
    type_preference_stack = (
        "current",
        "original",
    )

    primary_title_lanague = None

    title_dict = {}
    output_description = ""

    # Now get the rest of the titles
    for language in language_preference_stack:
        language_code = three_to_two_iso_code[language]
        language_titles = titles.get(language)

        # No lanague
        if language_titles is None:
            continue

        # If we've already set a title for this language, move on
        if language_code in title_dict:
            continue

        # We only take one title per language, in preference order
        for type_of_title in type_preference_stack:
            try:
                specific_titles = language_titles[type_of_title]
            except KeyError:
                continue
            else:
                break

        # Illustrations for books have double titles, but one is a
        # description that contains "illustration"
        for title in specific_titles:
            # Set description
            if "illustrasjon" in title.lower():
                output_description = f"{{{{{language_code}|{title}}}}}"
                continue
            # Else it's a title, and we never have more than two items
            else:
                title_dict[language_code] = title.title()

                if primary_title_lanague is None:
                    primary_title_lanague = language_code

    # Now put together templates into a string
    primary_title = title_dict.pop(primary_title_lanague)
    other_languages = "\n".join([f"|{lc}={title}" for lc, title in title_dict.items()])

    output = textwrap.dedent(
        f"""
        {{{{Title
          |1={primary_title}
          |lang={primary_title_lanague}
          {other_languages}
        }}}}
        """
    ).strip("\n")


    return output, output_description


def get_sources(
    nasjonalmuseet_link: str, digitalt_museum_link: str, direct_image_link: str
) -> str:
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
    if not subjects:
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


def get_json_blob(raw_data: str) -> str:
    code_template = textwrap.dedent(
        f"""
        <!--{raw_data}-->
        """
    ).strip("\n")

    return code_template


data_dir = "./data/our_parsed_data/enriched/"

for filename in sorted(os.listdir(data_dir)):
    if filename.endswith(".json"):
        with open(os.path.join(data_dir, filename)) as f:
            data = json.load(f)

        # Creation_date
        date_json = data.get("creation_date")
        date = ""
        if date_json:
            date = get_date(date_json)

        # Medium
        techniques_json = data.get("techniques")
        materials_json = data.get("materials")
        medium = get_medium(techniques_json, materials_json)

        # Size
        measurements_json = data.get("measurements")
        dimensions = get_dimensions(measurements_json)

        # Location
        locations_json = data.get("locations")
        if locations_json is not None:
            locations_json = locations_json.get("depicted_location")
            depicted_place = get_depicted_place(locations_json)
        else:
            depicted_place = ""

        # Title
        titles_json = data.get("titles")
        title, description = get_title_and_description(titles_json)

        # Source
        nasjonalmuseet_link = data["nasjonalmuseet_link"]
        digitalt_museum_link = data["digitalt_museum_link"]
        direct_image_link = data["picture"]["direct_image_link"]

        source = get_sources(nasjonalmuseet_link, digitalt_museum_link, direct_image_link)

        # Accession number
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

        # Credit line
        acquistion_notes = data.get("acquistion_notes")
        credit_line = get_credit_line(acquistion_notes)

        # Subjects
        subjects = data.get("subjects")
        other_fields = get_other_fields(subjects)

        # Photographer
        photographer = data["picture"].get("photographer")
        if photographer is None:
            photographer = ""
        else:
            photographer = "/" + photographer

        # raw_data
        raw_data = get_json_blob(data)

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
            raw_data=raw_data,
            photographer=photographer,
        )
        print("-----------------------------------")
        print(wiki_template)
