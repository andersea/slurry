"""Asynchronous generators for testing sections."""
import string

import trio

async def produce_increasing_integers(interval, *, max=3, delay=0):
    await trio.sleep(delay)
    for i in range(max):
        yield i
        if i == max-1:
            break
        await trio.sleep(interval)

async def produce_alphabet(interval, *, max=3, delay=0):
    await trio.sleep(delay)
    for i, c in enumerate(string.ascii_lowercase):
        yield c
        if i == max - 1:
            break
        await trio.sleep(interval)

async def spam_wait_spam_integers(interval):
    async for i in produce_increasing_integers(.1, max=5, delay=.1):
        yield i
    await trio.sleep(interval)
    async for i in produce_increasing_integers(.1, max=5, delay=.1):
        yield i

async def produce_mappings(interval):
    vehicles = [
        {'vehicle': 'motorcycle'},
        {'vehicle': 'car'},
        {'vehicle': 'motorcycle'},
        {'vehicle': 'autocamper'},
        {'vehicle': 'car'},
        {'vehicle': 'car'},
        {'vehicle': 'truck'},
        {'vehicle': 'car'},
        {'vehicle': 'motorcycle'},
    ]

    for i, vehicle in enumerate(vehicles):
        vehicle['number'] = i
        yield vehicle
        await trio.sleep(interval)
