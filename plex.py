from plexapi.myplex import MyPlexAccount
from config import dvrConfig
import logging


class plex:
    def __init__(self):
        self.logger = logging.getLogger("PlexAPI")
        try:
            account = MyPlexAccount(dvrConfig['Plex']['username'], dvrConfig['Plex']['password'])
            self.plex = account.resource(dvrConfig['Plex']['server']).connect()
        except Exception as e:
            self.logger.error("Unable to connect to Plex Server VIA MyPlex")
            self.plex = None

    def getDVR(self):
        if self.plex is None:
            return None
        self.logger.debug("Requesting PlexServer DVRs" )
        res = self.plex.query("/livetv/dvrs/", self.plex._session.get)
        if len(res) == 0:
            self.logger.warning("Unable to extract DVR ID from Plex. Please manually set")
            return None
        elif len(res) == 1:
            id = str(res[0].get("key"))
            self.logger.debug("Found Plex DVR ID %s" % id)
            return id
        else:
            ids = [str(r.get("key")) for r in res]
            print("Found multiple Plex DVRs, please manually configure with an ID of either %s" % str(ids))
            return None

    def refreshEPG(self):
        if self.plex is None:
            return None
        try:
            dvr = self.getDVR()
            if dvr is None:
                dvr = dvrConfig["Plex"]["dvrID"]
        except:
            self.logger.warning("Error occurred when getting Plex DVR ID")
            dvr = dvrConfig["Plex"]["dvrID"]
        self.logger.debug("Requesting PlexServer update EPG for DVR %s " % str(dvr))
        try:
            self.plex.query("/livetv/dvrs/%s/reloadGuide" % str(dvr), self.plex._session.post)
        except Exception as e:
            self.logger.error("Error occurred when updating Plex EPG")


def refreshEPG():
    if dvrConfig.get('Plex', {"enable": False})['enable']:
        p = plex()
        p.refreshEPG()
