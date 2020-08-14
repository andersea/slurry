import string

import trio

async def produce_increasing_integers(interval, *, max=3):
    for i in range(max):
        yield i
        if i == max-1: break
        await trio.sleep(interval)

async def produce_alphabet(interval, *, max=3):
    for i, c in enumerate(string.ascii_lowercase):
        yield c
        if i == max - 1: break
        await trio.sleep(interval)