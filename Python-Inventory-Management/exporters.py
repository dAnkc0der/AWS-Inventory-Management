import json, csv

def export_to_json(data, filename):
    """
    Converts to .json file
    """
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

def export_to_csv(data, filename):
    """
    Converts to .csv file
    """
    if not data:
        return
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys()) 
        writer.writeheader()
        writer.writerows(data)

def export_all(data, base_filename):
    """
    Exports the given data to both JSON and CSV using the same base filename.
    Args: data (list[dict]), base_filename (str, without extension)
    Returns: None
    """
    export_to_json(data, f"{base_filename}.json")
    export_to_csv(data, f"{base_filename}.csv")
