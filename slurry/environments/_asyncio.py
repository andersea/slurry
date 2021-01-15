"""Asyncio environment for slurry."""
import asyncio
from collections import deque
from socket import socketpair
from threading import Thread


from typing import Any, AsyncIterable, Awaitable, Callable, Optional

import trio
from trio.lowlevel import current_trio_token

from ..sections.abc import AsyncSection

MESSAGE_CLOSE = b'\x04'
MESSAGE_ENQUEUED = b'\x05'
MESSAGE_DEQUEUED = b'\x06'

class AsyncioSection(AsyncSection):
    _loop_lock = trio.Lock()
    _loop = None

    async def pump(self, input: Optional[AsyncIterable[Any]], output: Callable[[Any], Awaitable[None]]):
        await self._ensure_loop()
        await self._trio_run_refine(input, output)

    async def _ensure_loop(self) -> None:
        async with self._loop_lock:
            if not self._loop:
                trio_token = current_trio_token()
                loop_running = trio.Event()
                loop_daemon = Thread(target=asyncio.run, args=(self._setup_asyncio_loop(trio_token, loop_running),), daemon=True)
                loop_daemon.start()
                await loop_running.wait()

    async def _setup_asyncio_loop(self, trio_token, loop_running):
        self._loop = asyncio.get_running_loop()
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
                await sock.send(MESSAGE_ENQUEUED)
                await sock.recv(1)
            await sock.send(MESSAGE_CLOSE)

        if input:
            asyncio.run_coroutine_threadsafe(
                self._asyncio_run_refine(send_queue, send_sockets[1], recv_queue, recv_sockets[1]),
                self._loop)
        else:
            asyncio.run_coroutine_threadsafe(
                self._asyncio_run_refine(None, None, recv_queue, recv_sockets[1]),
                self._loop)

        async with trio.open_nursery() as nursery:
            if input:
                nursery.start_soon(send_task)
            sock = trio.socket.from_stdlib_socket(recv_sockets[0])
            while True:
                byt = await sock.recv(1)
                if byt == MESSAGE_CLOSE:
                    break
                await output(recv_queue.pop())
                await sock.send(MESSAGE_DEQUEUED)
            nursery.cancel_scope.cancel()

    async def _asyncio_run_refine(self, input_queue, input_socket, output_queue, output_sock):
        async def asyncio_input():
            while True:
                byt = await self._loop.sock_recv(input_socket, 1)
                if byt == MESSAGE_CLOSE:
                    break
                yield input_queue.pop()
                await self._loop.sock_sendall(input_socket, MESSAGE_DEQUEUED)

        async def asyncio_output(item):
            output_queue.appendleft(item)
            await self._loop.sock_sendall(output_sock, MESSAGE_ENQUEUED)
            await self._loop.sock_recv(output_sock, 1)

        if input_queue:
            await self.refine(asyncio_input(), asyncio_output)
        else:
            await self.refine(None, asyncio_output)
        await self._loop.sock_sendall(output_sock, MESSAGE_CLOSE)
