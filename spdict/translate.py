from __future__ import barry_as_FLUFL

import asyncio
import sys
import time
from typing import *

import aiohttp
from bs4 import BeautifulSoup
from tabulate import tabulate


url = "https://www.spanishdict.com"


async def r_get(url: str, session: aiohttp.ClientSession) -> aiohttp.client_reqrep.ClientResponse:
    """Asyncronous get"""
    return await session.request(method="GET", url=url)


async def translate(word: str, session: aiohttp.ClientSession) -> List[str]:
    """
    Translates a word to english or spanish.

    :param word: the english or spanish word to translate
    :return: the possible translations
    """
    try:
        r = await r_get(f"{url}/translate/{word}", session)
        soup = BeautifulSoup(await r.text(), "html.parser")
        # translation_div > _ > _ > quickdef
        translation_div = soup.find("div", {"class": "quickdefsWrapperDesktop--fy8K_XyV"})
        # quickdef > translations
        res = [element.contents[0]
                for element in
                translation_div.find_all('a', {"class": "a--3Le9u96E"})]
        return res
    except Exception:
        return ["TODO"]


async def mass_translate(words: List[str]) -> List[List[str]]:
    """
    Mass translate words to english or spanish.

    :param words: the english or spanish words to translate
    :return: the list of translations
    """
    async with aiohttp.ClientSession() as session:
        return await asyncio.gather(*(translate(word, session) for word in words))


async def main(words: List[str]) -> None:
    raw = words[0] == "--raw"
    try:
        translations = await mass_translate(words[1:] if raw else words)
    except Exception as e:
        translations = [[]] * len(words)

    if raw:
        print(*(','.join(t) for t in translations), sep='\n')
    else:
        print(tabulate({
            "Original": words,
            "Translated": [', '.join(t) for t in translations]},
            headers="keys", tablefmt="fancy_grid"))


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))

