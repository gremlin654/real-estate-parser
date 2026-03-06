import asyncio
from app.scraper.kufar_client import KufarAPIClient

async def test():
    client = KufarAPIClient()
    result = await client.fetch_listings('mogilev', 1)
    if result and 'items' in result:
        print(f'Total items: {len(result["items"])}')
        print('---')
        for i, item in enumerate(result['items'][:5]):
            print(f'Item {i}:')
            print(f'  price: {item.get("price")}')
            print(f'  price_usd: {item.get("price_usd")}')
            print(f'  price$: {item.get("price$")}')
            print(f'  title: {item.get("title", "")[:50]}')
            print(f'  currency: {item.get("currency")}')
            print('  ---')

asyncio.run(test())
