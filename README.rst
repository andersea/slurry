======
Slurry
======

.. image:: https://readthedocs.org/projects/slurry/badge/?version=latest
   :target: https://slurry.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

.. image:: https://img.shields.io/pypi/v/slurry.svg
   :target: https://pypi.org/project/slurry
   :alt: Latest PyPi version

.. image:: https://github.com/andersea/slurry/workflows/build/badge.svg
   :target: https://github.com/andersea/slurry
   :alt: Build Status

An async stream processing microframework for Python

Introduction
------------

Slurry_ builds on the concepts of structured concurrency and memory channels, originating in
Trio_, and uses them to create a microframework for processing streaming data.

The basic building blocks of Slurry includes:

- **Pipelines** - An asynchronous context manager which encapsulates a stream process.
- **Sections** - The individual processing steps.
- **Taps** - Output channels for the processed stream.
- **Extensions** - A way to add more processing steps to an existing pipeline.

Slurry avoids using asynchronous generator functions, in favor of the pull-push programming style
of memory channels. It can be thought of as an asynchronous version of itertools_ - on steroids!

Included in the basic library are a number of basic stream processing building blocks, like
``Map``, ``Chain``, ``Merge`` and ``Zip``, and it is easy to build your own!

Demonstration
-------------
Enough talk! Time to see what's up!

.. code-block:: python

   async with Pipeline.create(
        Zip(produce_increasing_integers(1, max=3), produce_alphabet(0.9, max=3))
    ) as pipeline, pipeline.tap() as aiter:
            results = [item async for item in aiter]
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

Slurry is tested on Python 3.7 or greater and requires the Trio_ concurrency and IO library.

License
-------
Slurry is licensed under the `MIT license`_.

.. _Slurry: https://github.com/andersea/slurry
.. _Trio: https://github.com/python-trio/trio
.. _itertools: https://docs.python.org/3/library/itertools.html
.. _PyPI: https://pypi.org/
.. _readthedocs: https://slurry.readthedocs.io/
.. _`source code`: https://github.com/andersea/slurry
__ `source code`_
.. _AnyIO: https://github.com/agronholm/anyio
.. _MIT license: https://github.com/andersea/slurry/blob/master/LICENSE

