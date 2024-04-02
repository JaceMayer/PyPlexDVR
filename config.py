import yaml


# Loads and provides dictionary access to the config
with open("config.yaml", 'r') as stream:
    dvrConfig = yaml.safe_load(stream)
