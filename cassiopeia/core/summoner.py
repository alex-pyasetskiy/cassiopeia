import os
import datetime
from PIL.Image import Image as PILImage

from merakicommons.ghost import ghost_load_on
from merakicommons.cache import lazy, lazy_property
from merakicommons.container import searchable, SearchableList

from ..configuration import settings
from ..data import Region, Platform
from .common import DataObject, CassiopeiaObject, CassiopeiaGhost
from ..dto.summoner import SummonerDto
from .staticdata.version import VersionListData

try:
    import ujson as json
except ImportError:
    import json


_profile_icon_names = None


##############
# Data Types #
##############


class ProfileIconData(DataObject):
    _renamed = {"id": "profileIconId"}

    @property
    def id(self) -> int:
        return self._dto["profileIconId"]


class AccountData(DataObject):
    _renamed = {"id": "accountId"}

    @property
    def id(self) -> int:
        return self._dto["id"]


class SummonerData(DataObject):
    _dto_type = SummonerDto
    _renamed = {"profile_icon": "profileIconId", "level": "summonerLevel", "revision_date": "revisionDate", "account": "accountId"}

    @property
    def region(self) -> str:
        return self._dto["region"]

    @property
    def account(self) -> AccountData:
        return AccountData({"id": self._dto["accountId"]})

    @property
    def id(self) -> int:
        return self._dto["id"]

    @property
    def name(self) -> str:
        return self._dto["name"]

    @property
    def level(self) -> str:
        return self._dto["summonerLevel"]

    @property
    def profile_icon(self) -> ProfileIconData:
        """ID of the summoner icon associated with the summoner."""
        return ProfileIcon(id=self._dto["profileIconId"])

    @property
    def revision_date(self) -> datetime.date:
        """Date summoner was last modified specified as epoch milliseconds. The following events will update this timestamp: profile icon change, playing the tutorial or advanced tutorial, finishing a game, summoner name change."""
        return self._dto["revisionDate"]


##############
# Core Types #
##############


class ProfileIcon(CassiopeiaObject):
    _data_types = {ProfileIconData}

    @property
    def id(self) -> int:
        return self._data[ProfileIconData].id

    @property
    def name(self) -> str:
        global _profile_icon_names
        if _profile_icon_names is None:
            module_directory = os.path.dirname(os.path.realpath(__file__))
            module_directory, _ = os.path.split(module_directory)  # Go up one directory
            filename = os.path.join(module_directory, 'profile_icon_names.json')
            _profile_icon_names = json.load(open(filename))
            _profile_icon_names = {int(key): value for key, value in _profile_icon_names.items()}
        try:
            return _profile_icon_names[self._data[ProfileIconData].id]
        except KeyError:
            return None

    @property
    def url(self) -> str:
        versions = settings.pipeline.get(VersionListData, query={"platform": settings.default_platform})
        return "http://ddragon.leagueoflegends.com/cdn/{version}/img/profileicon/{id}.png".format(version=versions[0], id=self.id)

    @property
    def image(self) -> PILImage:
        return settings.pipeline.get(PILImage, query={"url": self.url})


class Account(CassiopeiaObject):
    _data_types = {AccountData}

    @property
    def id(self) -> int:
        return self._data[AccountData].id


@searchable({str: ["name"], int: ["id", "accountId"]})
class Summoner(CassiopeiaGhost):
    _data_types = {SummonerData}

    def __init__(self, *args, **kwargs):
        if "region" not in kwargs and "platform" not in kwargs:
            kwargs["region"] = settings.default_region.value
        super().__init__(*args, **kwargs)

    @lazy_property
    def region(self) -> Region:
        """The region for this champion."""
        return Region(self._data[SummonerData].region)

    @lazy_property
    def platform(self) -> Platform:
        """The platform for this champion."""
        return self.region.platform

    @CassiopeiaGhost.property(SummonerData)
    @ghost_load_on(KeyError)
    @lazy
    def account(self) -> Account:
        return Account(self._data[SummonerData].account)

    @CassiopeiaGhost.property(SummonerData)
    @ghost_load_on(KeyError)
    def id(self) -> int:
        return self._data[SummonerData].id

    @CassiopeiaGhost.property(SummonerData)
    @ghost_load_on(KeyError)
    def name(self) -> str:
        return self._data[SummonerData].name

    @CassiopeiaGhost.property(SummonerData)
    @ghost_load_on(KeyError)
    def level(self) -> str:
        return self._data[SummonerData].level

    @CassiopeiaGhost.property(SummonerData)
    @ghost_load_on(KeyError)
    def profile_icon(self) -> ProfileIcon:
        return self._data[SummonerData].profile_icon

    @CassiopeiaGhost.property(SummonerData)
    @ghost_load_on(KeyError)
    @lazy
    def revision_date(self) -> datetime.date:
        return datetime.datetime.fromtimestamp(self._data[SummonerData].revision_date / 1000)

    # Special core methods

    @lazy_property
    def champion_masteries(self):
        from .championmastery import ChampionMastery
        from ..dto.staticdata.champion import ChampionListDto
        # We don't need the entire champion data, we just need the dtos
        champions = settings.pipeline.get(ChampionListDto, query={"region": self.region, "platform": self.platform.value, "tags": {"all"}})
        champions = champions["data"].values()
        return SearchableList([ChampionMastery(summoner=self, champion=champion["id"]) for champion in champions])

    @lazy_property
    def mastery_pages(self):
        from .masterypage import MasteryPagesData, MasteryPage
        mastery_pages = settings.pipeline.get(MasteryPagesData, query={"summonerId": self.id, "region": self.region.value, "platform": self.platform.value})
        for i, page in enumerate(mastery_pages):
            mastery_pages[i] = MasteryPage(data=page)
        return SearchableList(mastery_pages)

    @lazy_property
    def rune_pages(self):
        from .runepage import RunePagesData, RunePage
        rune_pages = settings.pipeline.get(RunePagesData, query={"summonerId": self.id, "region": self.region.value, "platform": self.platform.value})
        for i, page in enumerate(rune_pages):
            rune_pages[i] = RunePage(data=page)
        return SearchableList(rune_pages)

    #def league(self):
    #    raise NotImplemented
    #def league_entry(self):
    #    raise NotImplemented
    #def matches(self):
    #    raise NotImplemented
    #def current_game(self):
    #    raise NotImplemented