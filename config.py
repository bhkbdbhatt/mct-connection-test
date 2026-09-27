import json

def load_country_config(file_path='country_config.json'):
    with open(file_path) as config_file:
        return json.load(config_file)

def get_credentials(country_code, config):
    return config.get(country_code, {})