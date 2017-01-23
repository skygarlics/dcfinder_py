import aiohttp
import asyncio
from aiohttp import ClientSession


urls = ['http://dcinside.com','http://google.com', 'http://naver.com']
async def main(url):
    async with aiohttp.get(url) as response:
        r = await response.read()
        print(url)

if __name__ == '__main__':
    tasks = []
    for url in urls:
        task = main(url)
        tasks.append(task)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait(tasks))