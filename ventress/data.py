import re
import aiohttp

class SurvivrData:
    class UserDoesNotExist(Exception): pass

    valid_intevals = ['all', 'alltime', 'weekly', 'daily']
    valid_gamemodes = range(-1, 19)

    def __init__(self, username, interval='all', gamemode=-1):
        self._username = username
        if interval not in self.valid_intevals:
            raise ValueError(f'{interval!r} is not a valid interval')
        self.interval = interval
        if gamemode not in self.valid_gamemodes:
            raise ValueError(f'{gamemode!r} is not a valid gamemode option.')
        self.gamemode = gamemode
        self.payload = {
            'slug': self._username.lower(),
            'interval': self.interval,
            'mapIdFilter': self.gamemode
        }

    def __await__(self):
        return self._async_init().__await__()

    async def _async_init(self):
        await self.json
        return self

    @property
    async def json(self):
        class ModesList(list): pass

        async with aiohttp.ClientSession() as session:
            async with session.post('https://surviv.io/api/user_stats', json=self.payload) as user:
                self._json = await user.json()
        if self._json is None:
            raise self.UserDoesNotExist(f'User {self._username!r} does not exist!')

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

        return self._json
