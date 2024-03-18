import io
import yaml

class config:
    def __init__(self):
        with open("config.yaml", 'r') as stream:
            self.config = yaml.safe_load(stream)

    def __getitem__(self, item):
        return self.config[item]


dvrConfig = config()
