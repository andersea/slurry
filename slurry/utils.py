"""Miscelaneous generators that doesn't fit the Mixer-Refiner pattern.

Can be used as pipeline input."""
import trio

async def repeat(interval, item):
    """Yields a single item repeatedly at regular intervals."""
    while True:
        yield item
        await trio.sleep(interval)
