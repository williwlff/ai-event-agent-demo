def merge_event(current: dict, new: dict) -> dict:
    for key, value in new.items():
        if isinstance(value, dict):
            current[key] = merge_event(
                current.get(key, {}), value
            )
        elif isinstance(value, list):
            current[key] = value
        else:
            current[key] = value
    return current
