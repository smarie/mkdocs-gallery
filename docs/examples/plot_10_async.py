"""
# Async support
"""

import asyncio
import time

start = time.time()
await asyncio.sleep(1)
stop = time.time()
f"I waited for {stop - start} seconds!"


# %%
# ## Async Iterator

class AsyncIterator:
    async def __aiter__(self):
        for chunk in "I'm an async iterator!".split():
            yield chunk


async for chunk in AsyncIterator():
    print(chunk, end=" ")

# %%
# ## Async comprehensions

" ".join([chunk async for chunk in AsyncIterator()])

# %%
# ## Async content manager


class AsyncContextManager:
    async def __aenter__(self):
        print("Entering ...")
        return self

    async def __aexit__(self, *exc_info):
        print("Exiting ...")

    def __str__(self):
        return "I'm an async context manager!"


async with AsyncContextManager() as acm:
    print(acm)
