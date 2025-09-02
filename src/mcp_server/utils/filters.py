from typing import Optional, Union, List, Any
from datetime import datetime, date, time

def is_nested_filter(item):
    if not isinstance(item, list) or len(item) < 2:
        return False
    return item[0] in ['and', 'or', 'not', '=', '<>', '<', '>', '<=', '>=', 'in', 'like', 'within', 'fuzzy']


# function to convert ISO format datetime strings to correct python object as per table schema
def parse_temporal_filters(filters: List[List[Any]], schema: List[dict]) -> List[List[Any]]:
    if not isinstance(filters, list):
        return filters  # Base case
    result = []
    for f in filters:
        if len(f) == 3:
            # Could be an operator like ["or", [...], [...]] or a comparison like ["<", "time", "2025-01-01..."]
            op, left, right = f
            col = None if isinstance(left, list) else left
            left = parse_temporal_filters([left], schema)[0] if isinstance(left, list) else left
            if isinstance(right, list):
                if is_list_of_iso_datetimes(right):
                   right= [cast_temporal_value(col, val, schema) for val in right]
                elif is_nested_filter(right):
                    right = parse_temporal_filters([right], schema)[0]
            else:
                right = cast_temporal_value(col, right, schema)
            result.append([op, left, right])

        elif len(f) == 2:
            # Unary operation like ["not", [...]]
            op, inner = f
            result.append([op, parse_temporal_filters([inner], schema)[0]])

        else:
            # Unexpected structure — recurse on every item
            result.append(f)

    return result

# checks if string is iso datetime format or not
def is_list_of_iso_datetimes(lst):
    if not isinstance(lst, list):
        return False
    try:
        for item in lst:
            if not isinstance(item, str):
                return False
            datetime.fromisoformat(item.replace("Z", "+00:00"))  # handles 'Z' for UTC
        return True
    except Exception:
        return False

# converts ISO datetime string to correct python type
def cast_temporal_value(col, val, schema):
    # Create a mapping from column name to column type
    type_map = {col["name"]: col["type"] for col in schema}
    # Known datetime-like types
    datetime_types = {"datetime", "datetime64[ns]", "date", "time"}
    if col is None:
        field_type = "datetime64[ns]" # default type
    else:
        field_type = type_map.get(col)
    result = val
    if field_type in datetime_types:
        if field_type in {"datetime", "datetime64[ns]"}:
            result = datetime.fromisoformat(val.replace("Z", "+00:00"))
        elif field_type == "date":
            result = date.fromisoformat(val.split("T")[0])
        elif field_type == "time":
            result = time.fromisoformat(val.split("T")[1])
    return result