"""
Using asyncio, create the 424 error, not enough pg connections.
"""

# Standard library
import argparse
import asyncio

# Custom package
import httpx

from nrcan_ssl.ssl_utils import SSLUtils


async def main(level: str = "dev", repeat: int = 15, sleep: int = 1):
    su = SSLUtils()
    su.set_nrcan_ssl()
    # large number of returns, takes time, not a good way to test multiple connections at the same time.
    stac_endpoint = "/stac/api/search?limit=1000"
    # Small number of returns, fast, better way to test multiple connections at the same time.
    stac_search = "/stac/api/search"
    stac_collections = "/stac/api/collections"

    if level == "stage":
        root = "https://datacube-stage.services.geo.ca"
    elif level == "prod":
        root = "https://datacube.services.geo.ca"
    else:
        root = "https://datacube-dev.services.geo.ca"

    search = root + stac_search
    collections = root + stac_collections
    for i in range(0, 25):
        await run_it(url=search, repeat=repeat, sleep=sleep)
    for j in range(0, 25):
        await run_it(url=collections, repeat=repeat, sleep=sleep)

    su.unset_nrcan_ssl()


async def run_it(url: str, repeat: int, sleep: int):
    for i in range(0, repeat):
        sc = await get_status_code(url)
        if sc == 200:
            print(sc)
        else:
            print(f"{sc}: {url}")
        if int(sleep) > 0:
            await asyncio.sleep(int(sleep))


async def get_status_code(url: str):
    async with httpx.AsyncClient() as client:
        r = await client.get(url, timeout=600)
        return r.status_code


async def _handle_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("-l", "--release_level", default="dev")
    parser.add_argument("-r", "--repeat", default=15)
    parser.add_argument("-s", "--sleep", default=1)

    args = parser.parse_args()

    await main(level=args.release_level, repeat=args.repeat, sleep=args.sleep)


if __name__ == "__main__":
    asyncio.run(_handle_args())
