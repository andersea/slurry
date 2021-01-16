"""Asyncio environment for slurry."""
import asyncio
from collections import deque
from socket import socketpair
from threading import Thread
from functools import partial


from typing import Any, AsyncIterable, Awaitable, Callable, Optional

import trio
from trio.lowlevel import current_trio_token

from ..sections.abc import AsyncSection

import logging

class AsyncioSection(AsyncSection):
    _loop_lock = trio.Lock()
    _loop = None

    async def pump(self, input: Optional[AsyncIterable[Any]], output: Callable[[Any], Awaitable[None]]):
        await self._ensure_loop()
        await self._trio_run_refine(input, output)

    async def _ensure_loop(self) -> None:
        async with self._loop_lock:
            if not self._loop:
                loop_running = trio.Event()
                loop_daemon = Thread(
                    target=asyncio.run,
                    args=(self._setup_asyncio_loop(current_trio_token(), loop_running),),
                    name='Asyncio Loop',
                    daemon=True)
                loop_daemon.start()
                await loop_running.wait()

    async def _setup_asyncio_loop(self, trio_token, loop_running):
        AsyncioSection._loop = asyncio.get_running_loop()
        trio.from_thread.run_sync(loop_running.set, trio_token=trio_token)
        quit = asyncio.Event()
        await quit.wait()

    async def _trio_run_refine(self, input, output):
        send_sockets = socketpair()
        send_queue = deque()
        recv_sockets = socketpair()
        recv_queue = deque()

        async def send_task():
            sock = trio.socket.from_stdlib_socket(send_sockets[0])
            async for item in input:
                send_queue.appendleft(item)
                await sock.send(b'\x00')
                await sock.recv(1)
            sock.close()

        async def recv_task():
            sock = trio.socket.from_stdlib_socket(recv_sockets[0])
            while True:
                if not await sock.recv(1):
                    break
                await output(recv_queue.pop())
                await sock.send(b'\x00')

        async with trio.open_nursery() as nursery:
            if input is not None:
                fut = asyncio.run_coroutine_threadsafe(
                    self._asyncio_run_refine(send_queue, send_sockets[1], recv_queue, recv_sockets[1]),
                    self._loop)
                nursery.start_soon(send_task)
            else:
                fut = asyncio.run_coroutine_threadsafe(
                    self._asyncio_run_refine(None, None, recv_queue, recv_sockets[1]),
                    self._loop)
            nursery.start_soon(recv_task)
            refine_done = trio.Event()
            trio_token = current_trio_token()
            fut.add_done_callback(lambda _: trio.from_thread.run_sync(refine_done.set, trio_token=trio_token))
            await refine_done.wait()
            return fut.result()

    async def _asyncio_run_refine(self, input_queue, input_socket, output_queue, output_sock):
        async def asyncio_input():
            while True:
                if not await self._loop.sock_recv(input_socket, 1):
                    break
                yield input_queue.pop()
                await self._loop.sock_sendall(input_socket, b'\x00')

        async def asyncio_output(item):
            output_queue.appendleft(item)
            await self._loop.sock_sendall(output_sock, b'\x00')
            await self._loop.sock_recv(output_sock, 1)

        if input_queue is not None:
            await self.refine(asyncio_input(), asyncio_output)
        else:
            await self.refine(None, asyncio_output)
        output_sock.close()
