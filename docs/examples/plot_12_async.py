"""
# Support for asynchronous code

[PEP 429](https://peps.python.org/pep-0492), which was first implemented in
[Python 3.5](https://docs.python.org/3/whatsnew/3.5.html#whatsnew-pep-492), added initial syntax for asynchronous
programming in Python: `async` and `await`. 

While this was a major improvement in particular for UX development, one major
downside is that it "poisons" the caller's code base. If you want to `await` a coroutine, you have to be inside a `async def`
context. Doing so turns the function into a coroutine function and thus forces the caller to also `await` its results.
Rinse and repeat until you reach the beginning of the stack.

Since version `0.10.0`, `mkdocs-gallery` is now able to automatically detect code blocks using async programming, and to handle them nicely so that you don't have to wrap them. This feature is enabled by default and does not require any configuration option. Generated notebooks remain consistent with [`jupyter` notebooks](https://jupyter.org/), or rather the [`IPython` kernel](https://ipython.org/) running
the code inside of them, that is equipped with 
[background handling to allow top-level asynchronous code](https://ipython.readthedocs.io/en/stable/interactive/autoawait.html).
"""

import asyncio
import time


async def afn():
    start = time.time()
    await asyncio.sleep(0.3)
    stop = time.time()
    return stop - start


f"I waited for {await afn():.1f} seconds!"


# %%
# Without any handling, the snippet above would trigger a `SyntaxError`, since we are using `await` outside of an
# asynchronous context. With the handling, it works just fine.
#
# The background handling will only be applied if it is actually needed. Meaning, you can still run your asynchronous
# code manually if required.

asyncio.run(afn())


# %%
# Apart from `await` all other asynchronous syntax is supported as well.
#
# ## Asynchronous Generators


async def agen():
    for chunk in "I'm an async iterator!".split():
        yield chunk


async for chunk in agen():
    print(chunk, end=" ")


# %%
# ## Asynchronous Comprehensions

" ".join([chunk async for chunk in agen()])

# %%
# ## Asynchronous Context Managers

import contextlib


@contextlib.asynccontextmanager
async def acm():
    print("Entering asynchronous context manager!")
    yield
    print("Exiting asynchronous context manager!")


async with acm():
    print("Inside the context!")
