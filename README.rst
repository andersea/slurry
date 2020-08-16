.. include: introduction.rst

Demonstration
-------------
Enough talk! Time to see what's up!

.. code-block:: python

   async with Pipeline.create(
        Zip(produce_increasing_integers(1, max=3), produce_alphabet(0.9, max=3))
    ) as pipeline, pipeline.tap() as aiter:
            results = []
            async for item in aiter:
                results.append(item)
            assert results == [(0,'a'), (1, 'b'), (2, 'c')]

The example producers (which are not part of the framework) could look like this:

.. code-block:: python

   async def produce_increasing_integers(interval, *, max=3):
      for i in range(max):
         yield i
         if i == max-1:
               break
         await trio.sleep(interval)

   async def produce_alphabet(interval, *, max=3):
      for i, c in enumerate(string.ascii_lowercase):
         yield c
         if i == max - 1:
               break
         await trio.sleep(interval)

Further documentation is available on readthedocs_. Check out the `source code`_ on github__.

Installation
------------
Still here? Wanna try it out yourself? Install from PyPI_::

   pip install slurry

Slurry is tested on Python 3.6 or greater. For now, Slurry is Trio only. AnyIO_ support is not
ruled out in the future.

.. _PyPI: https://pypi.org/
.. _readthedocs: https://slurry.readthedocs.io/
.. _`source code`: https://github.com/andersea/slurry
__ `source code`_
.. _AnyIO: https://github.com/agronholm/anyio

