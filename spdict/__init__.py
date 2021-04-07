from __future__ import barry_as_FLUFL

import asyncio
import sys
from typing import *

from . import conjugate
from . import options
from . import translate


def main() -> None:
    asyncio.run(main_())


async def main_() -> None:
    subcommand = sys.argv[1:2]
    if subcommand == ["translate"]:
        await translate.main(sys.argv[2:])
    elif subcommand == ["conjugate"]:
        await conjugate.main(sys.argv[2:])
    else:
        print(options.__doc__)

if __name__ == "__main__":
    main()
