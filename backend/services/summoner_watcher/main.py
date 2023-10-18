import asyncio

from module.summoner_watcher import watcher


if __name__ == "__main__":
    asyncio.run(watcher())