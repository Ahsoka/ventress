import re
import aiohttp

class JSONToClass:
    def __init__(self):
        raise NotImplementedError('You must define an __init__ method.')

    def __await__(self):
        return self._async_init().__await__()

    async def _async_init(self):
        await self._setattrs()
        if not self._json:
            return None
        return self

    async def _get_json(self):
        async with aiohttp.ClientSession() as session:
            async with session.post(type(self).url,
                                    json=self.payload,
                                    params=self.params if hasattr(self, 'params') else {}) as request:
                self._request = request
                return await request.json()

def code_block(string, lang='', ending_line=True):
    if lang is None:
        lang = ''
    # NOTE: char(10) is '\n'
    return f"```{lang}\n{string}{char(10) if ending_line else ''}```"
