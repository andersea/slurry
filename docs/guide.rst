=====
Guide
=====

Introduction
------------

The Slurry microframework is a foundation for building reactive data processing applications. Slurry provides building
blocks that allow you to take one or more asynchronous event-based data sources, and process those sources using a
variety of configurable components, called sections, and feeding the processed data to one or more consumers. One of
the key features of Slurry, is that processing occurs asynchronously in a task based fashion. This allows advanced time-based
components to be build, like for example sections that group input based on timers.

Slurry is inspired a mix of different ideas from programming paradigms such as functional programming, to IoT data processing
frameworks like Node-RED_, and graphical data science frameworks like KNIME_ and Alteryx_. From the python world, Slurry takes
inspiration from iteration libraries like the built-in module itertools_. When combined with asynchronous features, those
libraries has lead to more advanced tools like aiostream_, eventkit_ and asyncitertools_. Especially aiostream_ deserves
credit as an inspiration for a lot of the basic stream processing sections, that Slurry provides out of the box.

Slurry is build on top of the Trio_ asynchronous concurrency library. Most data processing components are expected to use
the new async/await features of python 3.5, and coroutines run inside a Trio task. However, functionality is provided that
allows synchronous blocking operations to occur, either in threads or in separate processes (with some standard limitations).

Slurry does not try to extend the python syntax by overloading operators. Everything is plain python with async/await syntax.

Oh, one final thing.. Maybe you are wondering - 'Why *Slurry*?' Well,
`wikipedia says <https://en.wikipedia.org/wiki/Slurry>`_ - "A slurry is
a mixture of solids denser than water suspended in liquid, usually water", and if you think about it,
data is kind of like solids of different shapes and sizes, and it flows through pipelines, kind of like a slurry, so there
we go.

Pipelines
---------

TODO: How to use pipelines.

Sections
--------

TODO: How to build custom sections.

.. _Node-RED: https://nodered.org/
.. _KNIME: https://www.knime.com/
.. _Alteryx: https://www.alteryx.com/
.. _itertools: https://docs.python.org/3/library/itertools.html
.. _aiostream: https://github.com/vxgmichel/aiostream
.. _eventkit: https://github.com/erdewit/eventkit
.. _asyncitertools: https://github.com/vodik/asyncitertools
.. _Trio: https://trio.readthedocs.io/en/stable/