"""
# Foo!

Bar? Baz!
"""

import asyncio
import time

start = time.time()
await asyncio.sleep(1)
stop = time.time()
f"I waited for {stop - start} seconds!"


#%%
# More code!

import asyncio
import time

start = time.time()
await asyncio.sleep(0.3)
stop = time.time()
f"I waited for {stop - start} seconds!"
