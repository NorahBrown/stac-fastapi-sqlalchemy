"""
Using asyncio, create the 424 error, not enough pg connections.
"""

# Standard library
import argparse
import concurrent.futures
import time

# Custom package
import httpx

from nrcan_ssl.ssl_utils import SSLUtils


def main(level: str = "dev", repeat: int = 15, sleep: int = 1):
    su = SSLUtils()
    su.set_nrcan_ssl()
    print("Running")
    # large number of returns, takes time, not a good way to test multiple connections at the same time.
    big_stac_search = "/stac/api/search?limit=1000"
    # Small number of returns, fast, better way to test multiple connections at the same time.
    stac_search = "/stac/api/search"
    stac_collections = "/stac/api/collections"

    if level == "stage":
        root = "https://datacube-stage.services.geo.ca"
    elif level == "prod":
        root = "https://datacube.services.geo.ca"
    else:
        root = "https://datacube-dev.services.geo.ca"

    big_search = root + big_stac_search
    search = root + stac_search
    collections = root + stac_collections
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for i in range(0, int(repeat)):
            futures.append(executor.submit(run_it, big_search, repeat, sleep))
            futures.append(executor.submit(run_it, search, repeat, sleep))
            futures.append(executor.submit(run_it, collections, repeat, sleep))

            if int(sleep) > 0:
                time.sleep(int(sleep))

        # for f in concurrent.futures.as_completed(futures):
        #     # print(f.result())

    su.unset_nrcan_ssl()
    print("Done")


def run_it(url: str, repeat: int, sleep: int):
    sc = get_status_code(url)
    if sc != 200:
        print(f"{sc}: {url}")


def get_status_code(url: str):
    r = httpx.get(url, timeout=600)
    return r.status_code


def _handle_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("-l", "--release_level", default="dev")
    parser.add_argument("-r", "--repeat", default=15)
    parser.add_argument("-s", "--sleep", default=1)

    args = parser.parse_args()

    main(level=args.release_level, repeat=args.repeat, sleep=args.sleep)


if __name__ == "__main__":
    _handle_args()
