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
