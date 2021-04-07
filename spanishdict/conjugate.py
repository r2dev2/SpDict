import asyncio
import itertools as it
from typing import *

import aiohttp
from bs4 import BeautifulSoup
from tabulate import tabulate


def get_conjugate_url(word: str) -> str:
    return f"https://www.spanishdict.com/conjugate/{word}"


async def r_get(url: str, session: aiohttp.ClientSession) -> aiohttp.client_reqrep.ClientResponse:
    return await session.request(method="GET", url=url)


async def get_participles(word: str, session: aiohttp.ClientSession) -> Dict[str, str]:
    try:
        r = await r_get(get_conjugate_url(word), session)
        soup = BeautifulSoup(await r.text(), "html.parser")
        # the table right above the indicative conjugation
        participles = soup.find("table", {"class": "participlesTable--9jeAZFrU"})
        culled = participles.find_all("a")
        present = str(culled[1].find("span").contents[0])
        past = str(culled[-1].find("span").contents[0])
        return {
            "Present": "None" if "<span" in present else present,
            "Past": "None" if "<span" in past else past
        }
    except Exception:
        return {"Present": "", "Past": ""}


def get_aria_of_tag(tag: BeautifulSoup) -> Optional[str]:
    try:
        return tag.get("aria-label")
    # Handle if tag is None
    except AttributeError:
        return None


def get_column_names(soup: BeautifulSoup) -> List[str]:
    return  [
        c.find('a').contents[0]
        # first tr second td > div > div
        for c in soup.find_all("div", {"class": "inlineTooltipWrapper--14F1yy0t"})
    ]


def get_conjugations_from_table(
        soup: BeautifulSoup) -> Dict[str, List[str]]:

    raw = [
        get_aria_of_tag(v.find('a'))
        # td > div
        for v in soup.find_all("div", {"class": "vtableWordContents--1fU54Tfk"})
    ]

    tenses = get_column_names(soup)
    result = dict()
    result[''] = ["yo", "tú", "Ud.",
                  "nosotros", "vosotros",
                  "Uds."]
    result.update({tense: [] for tense in tenses})

    for tense, value in zip(it.cycle(tenses), raw):
        result[tense].append(value)

    return result


async def get_conjugations(
        word: str, mood: int,
        session: aiohttp.ClientSession
        ) -> Dict[str, List[str]]:

    try:
        r = await r_get(get_conjugate_url(word), session)
        soup = BeautifulSoup(await r.text(), "html.parser")
        # #conjugation-content-wrapper > div > div > div > table
        conjugations = soup.find_all(
                "table", {"class": "vtable--2WLTGmgs"})
        return get_conjugations_from_table(conjugations[mood])
    except Exception:
        return {"": [""]}


async def main(args):
    async with aiohttp.ClientSession() as session:
        if args[0] in {'-p', "--participle"}:
            words = args[1:]
            parts = await asyncio.gather(*(get_participles(word, session) for word in words))
            print(tabulate({
                "Original": words,
                "Present": [p["Present"] for p in parts],
                "Past": [p["Past"] for p in parts]},
                headers="keys", tablefmt="fancy_grid"))

        else:
            try:
                mood = {
                    "indicative": 0,
                    "subjunctive": 1,
                    "imperative": 2,
                    "continuous": 3,
                    "perfect": 4,
                    "perfect-subjunctive": 5
                }[args[0].lower()]
                words = args[1:]
            except (IndexError, KeyError):
                mood = 0
                words = args[:]

            conjugations = await asyncio.gather(
                    *(get_conjugations(w, mood, session) for w in words))

            to_print = []
            for w, conj in zip(words, conjugations):
                table = tabulate(
                    conj, headers="keys", tablefmt="fancy_grid"
                )

                # Printing the word in a caption on the table
                top = table[:table.find("\n")]
                newtop = top[0] + top[1]*(len(top) - 2) + top[-1]
                spaces = ' '*((len(top)-len(w)) // 2 - 1)
                begspace = ' ' * ((len(top)-len(w)) % 2)

                to_print.append('\n'.join((
                    newtop,
                    f"|{spaces}{w}{spaces}{begspace}|",
                    table.replace(top[0], '╞').replace("═╕", '═╡')
                )))

            print('\n\n'.join(to_print))

