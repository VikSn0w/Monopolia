from Property import Property
import json
import os
import pathlib


def load_properties(properties_path):
    with open(properties_path, 'r', encoding='utf-8') as json_file:
        properties_data = json.load(json_file)

    return [Property(prop) for prop in properties_data]


if __name__ == "__main__":
    current_dir = pathlib.Path(__file__).parent
    path = current_dir.parent / 'loc' / 'en-us' / 'properties.json'

    properties_obj = load_properties(path)
    for prop in properties_obj:
        print(prop.name)