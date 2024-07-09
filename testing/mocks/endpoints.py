from ..client import async_client


async def new_match(url: str, json: dict):
    async with async_client() as client:
        return await client.post(url, json=json)


async def join(url: str, json: dict):
    async with async_client() as client:
        return await client.post(url, json=json)
