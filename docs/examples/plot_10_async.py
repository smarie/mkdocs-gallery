"""
# Support for asynchronous code

[PEP 429](https://peps.python.org/pep-0492), which was first implemented in
[Python 3.5](https://docs.python.org/3/whatsnew/3.5.html#whatsnew-pep-492), added
initial syntax for asynchronous programming in Python: `async` and `await`. While this
improved UX for asynchronous programming quite a bit, one major downside is that it
"poisons" your code base. If you want to `await` a coroutine, you have to be inside a
`async def` context. Doing so turns the function into a coroutine function and thus
forces the caller to also `await` its results. Rinse and repeat until you reach the
beginning of the stack.

While this might be acceptable for applications, e.g. a web framework, for scripts it is
usually a nuisance. [`jupyter` notebooks](https://jupyter.org/), or rather the
[`IPython` kernel](https://ipython.org/) running the code inside of them, have some
[background handling to allow top-level asynchronous code](https://ipython.readthedocs.io/en/stable/interactive/autoawait.html).

And so does `mkdocs-gallery` to keep examples that require asynchronous code nice and
clean.
"""

import asyncio
import time


async def fn():
    start = time.time()
    await asyncio.sleep(0.3)
    stop = time.time()
    return stop - start


f"I waited for {await fn():.1f} seconds!"


# %%
# Without any handling, the snippet above would trigger a `SyntaxError`, since we are
# using `await` outside of an asynchronous context. With the handling, it works just
# fine.
#
# The background handling will only be applied if it is actually needed. Meaning, you
# can still run your asynchronous code manually if required.

asyncio.run(fn())


# %%
# Apart from `await` all other asynchronous syntax is supported as well.
#
# ## Asynchronous Generators


async def gen():
    for chunk in "I'm an async iterator!".split():
        yield chunk


async for chunk in gen():
    print(chunk, end=" ")


# %%
# ## Asynchronous Comprehensions

" ".join([chunk async for chunk in gen()])

# %%
# ## Asynchronous Context Managers


class AsyncContextManager:
    async def __aenter__(self):
        print("Entering asynchronous context manager!")
        return self

    async def __aexit__(self, *exc_info):
        print("Exiting asynchronous context manager!")


async with AsyncContextManager():
    print("Inside the context!")
