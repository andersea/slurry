import string
from functools import wraps

import pytest
import trio

from .fixtures import AsyncIteratorWithoutAclose

def fixture_gen_with_and_without_aclose(async_gen):

    def fixture_func(_with_aclose):
        if _with_aclose:
            new_async_gen = async_gen
        else:
            @wraps(async_gen)
            def new_async_gen(*args, **kwargs):
                return AsyncIteratorWithoutAclose(async_gen(*args, **kwargs))
        return new_async_gen

    fixture_func.__name__ = async_gen.__name__
    fixture_func.__qualname__ = async_gen.__name__

    return pytest.fixture(fixture_func)

@pytest.fixture(params=[True, False], ids=["with_aclose", "without_aclose"])
def _with_aclose(request):
    return request.param

@fixture_gen_with_and_without_aclose
async def produce_increasing_integers(interval, *, max=3, delay=0):
    await trio.sleep(delay)
    for i in range(max):
        yield i
        if i == max-1:
            break
        await trio.sleep(interval)

@fixture_gen_with_and_without_aclose
async def produce_alphabet(interval, *, max=3, delay=0):
    await trio.sleep(delay)
    for i, c in enumerate(string.ascii_lowercase):
        yield c
        if i == max - 1:
            break
        await trio.sleep(interval)

@pytest.fixture()
def spam_wait_spam_integers(produce_increasing_integers):
    async def spam_wait_spam_integers(interval):
        async for i in produce_increasing_integers(.1, max=5, delay=.1):
            yield i
        await trio.sleep(interval)
        async for i in produce_increasing_integers(.1, max=5, delay=.1):
            yield i

    return spam_wait_spam_integers

@fixture_gen_with_and_without_aclose
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
