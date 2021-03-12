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

class Gamemode(str):
    def __new__(cls, gamemode, *args, **kwargs):
        if gamemode == -1 or isinstance(gamemode, str) and 'all' in gamemode:
            return None
        else:
            try:
                if isinstance(gamemode, (int, float)):
                    return super().__new__(cls, game_modes[int(gamemode)])
            except KeyError as error:
                raise ValueError(f'{gamemode} is not a valid gamemode option. '
                                  "Possible options are -1 to 11 and 13 to 18.") from error
            return super().__new__(cls, gamemode)

    def __init__(self, gamemode):
        self.encoded = gamemode
        self.proper = game_modes[self.encoded]
    
    def _set_encoded(self, value):
        if isinstance(value, (int, float)):
            self._encoded = int(value)
        elif isinstance(value, str):
            for num, mode in game_modes.items():
                if value.lower() in mode.lower():
                    self._encoded = num
                    break
            else:
                raise ValueError(f'{value!r} is not a valid gamemode option. See data.game_modes to see the valid options.')
        else:
            raise TypeError(f"gamemode must be a string or number, not a '{type(value)}'")
    
    def _get_encoded(self):
        return self._encoded
    
    encoded = property(_get_encoded, _set_encoded)

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
        
        self.gamemode = Gamemode(gamemode)

        self.payload = {
            'slug': self.slug,
            'interval': self.interval,
            'mapIdFilter': self.gamemode.encoded
        }

        self.url = self._instance_url()
    
    def _instance_url(self):
        if self.gamemode:
            return f"https://surviv.io/stats/{self.slug}?{urlencode({'t': self.interval, 'mapId': self.gamemode.encoded})}"
        else:
            return f"https://surviv.io/stats/{self.slug}?{urlencode({'t': self.interval})}"

    @property
    def how_recent(self):
        intervals = {
            'alltime': 'All Games',
            'weekly': 'Games in the Last Week',
            'daily': 'Games in the Last Day'
        }
        return intervals[self.interval]
    
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

    def overall_win_percentage(self, precision=2, hundred=True):
        return round(self.wins / self.games * 100, precision) if hundred else round(self.wins / self.games, precision)

    @property
    def embed_overall_stats(self):
        upper_portion = f"Wins: {self.wins}\tGames: {self.games}\tWin Percentage: {self.overall_win_percentage()}%"
        lower_portion = f"Kills: {self.kills}"
        lower_portion += ' ' * (len(upper_portion[:upper_portion.find('\t', upper_portion.find('\t') + 1) + 1].replace('\t', ' ' * 4)) - len(lower_portion)) \
                         + f'Kills Per Game (KPG): {self.kpg}'
        return code_block(f"{upper_portion}\n{lower_portion}", lang='py')

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
