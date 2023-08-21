from datetime import datetime
import json
import os


def get_creation_date(from_date, to_date, descriptive_date):
    # Have to use the descriptive_date if it is all we have
    if from_date is None and to_date is None:
        output_date = descriptive_date.strip("()")
        return {"range_of_dates": False, "created_at_date": output_date}

    # Otherwise figure out date precision
    from_date_dt = datetime.strptime(from_date, "%Y-%m-%d")
    to_date_dt = datetime.strptime(to_date, "%Y-%m-%d")

    from_day = from_date_dt.day
    from_month = from_date_dt.month
    from_year = from_date_dt.year
    to_day = to_date_dt.day
    to_month = to_date_dt.month
    to_year = to_date_dt.year

    # The museum used `01` as "unknown" dates, but also as real "01" dates.
    # We have to use descriptive_date to figure out which
    day_is_null = (from_day == 1 and to_day == 1) and not descriptive_date.startswith("1.")
    # We never have a NULL month if the day is known
    month_is_null = (from_month == 1 and to_month == 1) and day_is_null and "januar" not in descriptive_date.lower()

    day_is_precise = (from_day == to_day) and not day_is_null
    month_is_precise = (from_month == to_month) and not month_is_null
    year_is_precise = from_year == to_year

    # Exact date
    if day_is_precise and month_is_precise and year_is_precise:
        return {"range_of_dates": False, "created_at_date": to_date}

    # Exact month
    elif month_is_precise and year_is_precise:
        return {"range_of_dates": False, "created_at_date": datetime.strftime(to_date_dt, "%Y-%m")}

    # Range of months
    elif not month_is_precise and not month_is_null and day_is_null and year_is_precise:
        return {
            "range_of_dates": True,
            "created_at_date_start": datetime.strftime(from_date_dt, "%Y-%m"),
            "created_at_date_end": datetime.strftime(to_date_dt, "%Y-%m"),
        }

    # Exact year
    elif year_is_precise and month_is_null and day_is_null:
        return {"range_of_dates": False, "created_at_date": datetime.strftime(to_date_dt, "%Y")}

    # Range of years
    elif not year_is_precise:
        return {
            "range_of_dates": True,
            "created_at_date_start": datetime.strftime(from_date_dt, "%Y"),
            "created_at_date_end": datetime.strftime(to_date_dt, "%Y"),
        }

    return None


data_dir = "./data/our_parsed_data/raw/"
output_dir = "./data/our_parsed_data/enriched/"

for filename in sorted(os.listdir(data_dir)):
    if filename.endswith(".json"):
        with open(os.path.join(data_dir, filename)) as f:
            data = json.load(f)

        # Set creation_date
        descriptive_date = data.get("descriptive_date")
        from_date = data.get("from_date")
        to_date = data.get("to_date")

        data["creation_date"] = get_creation_date(from_date, to_date, descriptive_date)

        # Write output file
        uuid = data["uuid"]
        output_file = os.path.join(output_dir, f"{uuid}.json")
        with open(output_file, "w") as f:
            json.dump(data, f, indent=2, sort_keys=True)

