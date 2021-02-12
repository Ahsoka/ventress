import re
import aiohttp

class JSONToClass:
    def __init__(self):
        raise NotImplementedError('You must define an __init__ method.')

    def __await__(self):
        return self._async_init().__await__()

    async def _async_init(self):
        await self._setattrs()
        return self

    async def _setattrs(self):
        async with aiohttp.ClientSession() as session:
            async with session.post(self.url,
                                    json=self.payload,
                                    params=self.params if hasattr(self, 'params') else {}) as request:
                self._request = request
                self._json = await request.json()
        if self._json is None:
            self._raise_error_json_is_none()

        decimal = re.compile(r'\d+\.\d+')
        for key in self._json:
            if decimal.fullmatch(str(self._json[key])):
                setattr(self, key, float(self._json[key]))
            else:
                setattr(self, key, self._json[key])
