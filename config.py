import yaml
import os


# Loads and provides dictionary access to the config
with open("config.yaml", 'r') as stream:
    dvrConfig = yaml.safe_load(stream)

environKeys = ["plex_enable", "plex_username", "plex_password", "plex_server", "plex_dvrID",
               "server_useWatchdog", "epg_TVDBAPIKey", "epg_generate"]
for k in environKeys:
    v = os.environ.get(k)
    if v is not None:
        # environment variable overrides yaml config
        section = k.split("_")[0].title()
        key = k.split("_")[1]
        if v not in ("plex_enable", "server_useWatchdog", "epg_generate"):
            dvrConfig[section][key] = type(dvrConfig[section][key])(v)
        else:
            if v == "true":
                v = True
            else:
                v = False
            dvrConfig[section][key] = v
