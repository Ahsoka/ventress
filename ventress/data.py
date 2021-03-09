import re

from urllib.parse import urlencode
from dateutil.parser import isoparse
from .utils import JSONToClass, code_block

game_modes = {
    -1: 'All modes',
    0: 'Normal',
    1: 'Desert',
    2: 'Woods',
    3: '50v50',
    4: 'Potato',
    5: 'Savannah',
    6: 'Halloween',
    7: 'Cobalt',
    8: 'Snow',
    9: 'Valentine',
    10: 'Saint Patrick',
    11: 'Eggsplosion',
    13: 'May 4th',
    14: '50v50 Last Sacrifice',
    15: 'Storm',
    16: 'Beach',
    17: 'Contact',
    18: 'Inferno'
}

class SurvivrData(JSONToClass):
    url = 'https://surviv.io/api/user_stats'
    valid_intevals = ['all', 'alltime', 'weekly', 'daily']
    valid_gamemodes = range(-1, 19)

    def __init__(self, slug, interval='all', gamemode=-1):
        self.slug = slug.lower()
        if interval not in self.valid_intevals:
            raise ValueError(f'{interval!r} is not a valid interval')
        
        if interval == 'all':
            interval = 'alltime'
        self.interval = interval
        
        self.encoded_gamemode = self.convert_to_gamemode(gamemode)
        if self.encoded_gamemode not in self.valid_gamemodes:
            raise ValueError(f'{self.encoded_gamemode!r} is not a valid gamemode option.')
        self.gamemode = self.encoded_to_gamemode(self.encoded_gamemode)

        self.payload = {
            'slug': self.slug,
            'interval': self.interval,
            'mapIdFilter': self.encoded_gamemode
        }
    
        self.url = f"https://surviv.io/stats/{self.slug}?{urlencode({'t': self.interval, 'mapId': self.encoded_gamemode})}"
    
    @property
    def how_recent(self):
        intervals = {
            'alltime': 'All Games',
            'weekly': 'Games in the Last Week',
            'daily': 'Games in the Last Day'
        }
        return intervals[self.interval]

    @staticmethod
    def convert_to_gamemode(mode_as_str: str):
        # TODO: Add typo detection (possibly using Levenshtein distance)
        if isinstance(mode_as_str, (int, float)):
            return int(mode_as_str)
        mode_as_str = mode_as_str.lower()
        for num, mode in game_modes.items():
            mode = mode.lower()
            if mode_as_str in mode:
                return num

    @staticmethod
    def encoded_to_gamemode(encoded):
        return None if encoded == -1 else game_modes[encoded]
    
    async def _setattrs(self):
        self._json = await self._get_json()
        if self._json is None:
            return

        decimal = re.compile(r'\d+\.\d+')
        for key in self._json:
            if decimal.fullmatch(str(self._json[key])):
                setattr(self, key, float(self._json[key]))
            else:
                setattr(self, key, self._json[key])
        if hasattr(self, 'modes') and len(self.modes) >= 1:
            class ModeDict(dict): pass
            self.modes = [ModeDict(mode) for mode in self.modes]
            camel = re.compile('[a-z]+')
            Case = re.compile(r'[A-Z][a-z]+')
            for mode in self.modes:
                for key in mode:
                    if decimal.fullmatch(str(mode[key])):
                        setattr(mode, key, float(mode[key]))
                    else:
                        setattr(mode, key, mode[key])
                    match = Case.findall(key)
                    if match:
                        setattr(mode,
                                f"{'_'.join([camel.match(key).group(0), *map(str.lower, match)])}",
                                mode[key])

    @property
    def embed_overall_stats(self):
        return code_block(f"GAMES: {self.games}\tWINS: {self.wins}\tKPG: {self.kpg}\tKILLS: {self.kills}", lang='py')
        

class UserMatchHistory(JSONToClass):
    url = 'https://surviv.io/api/match_history'
    valid_team_modes = (1, 2, 4, 7)

    def __init__(self, slug, count, offset=0, team_mode=7):
        self.slug = slug.lower()
        self.count = count
        self.offset = offset
        if team_mode not in self.valid_team_modes:
            raise ValueError(f'{team_mode!r} is not a valid team mode.')
        self.team_mode = team_mode
        self.payload = {
            'slug': self.slug,
            'count': self.count,
            'offset': self.offset,
            'teamModeFilter': self.team_mode
        }
    
    def __len__(self):
        return len(self.games)
    
    def __getitem__(self, index):
        return self.games[index]
    
    async def _setattrs(self):
        self._json = await self._get_json()

        if self._json:
            class Game(dict): pass
            self.games = [Game(game) for game in self._json]
            for game in self.games:
                for attr in game:
                    # There are no decimals in this response
                    # we do not not need to check for them

                    # Try and convert to a datetime object
                    try:
                        setattr(game, attr, isoparse(game[attr]))
                    except (ValueError, TypeError):
                        setattr(game, attr, game[attr])
