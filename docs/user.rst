==========
User Guide
==========

Introduction
------------

The Slurry microframework is a foundation for building reactive data processing applications. Slurry provides building
blocks that allow you to take one or more asynchronous event-based data sources, and process those sources using a
variety of configurable components, called sections, and feeding the processed data to one or more consumers. One of
the key features of Slurry, is that processing occurs asynchronously in a task based fashion. This allows advanced time-based
components to be build, like for example sections that group input based on timers.

Slurry is inspired by a mix of different ideas from programming paradigms such as functional programming, IoT data processing
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
The :class:`Pipeline <slurry.Pipeline>` class is a composable stream processor. It consists of a chain of
``PipelineSection`` compatible objects, which each handle a single stream processing operation. Slurry
contains a helper function called `weld` that takes care of composing (welding) a
pipeline out of individual sections. A ``PipelineSection`` is any object that is valid input to the `weld`
function. This currently includes the following types:

AsyncIterables
  Async iterables are valid only as the very first ``PipelineSection``. Subsequent
  sections will use this async iterable as input source. Placing an ``AsyncIterable`` into the middle of
  a sequence of pipeline sections, will cause a ``ValueError``.
Sections
  Any :class:`Section <slurry.sections.abc.Section>` abc subclass is a valid ``PipelineSection``, at any
  position in the pipeline.
Tuples
  Pipeline sections can be nested to any level by supplying a ``Tuple[PipelineSection, ...]``
  containing one or more pipeline section-compatible objects. Output from upstream sections are
  automatically used as input to the nested sequence of pipeline sections.

.. note::
  The ``weld`` function is part of the developer api. See :func:`slurry.sections.weld.weld` for more information.

The stream processing results are accessed by calling :meth:`Pipeline.tap() <slurry.Pipeline.tap>` to create an
output channel. Each pipeline can have multiple open taps, each receiving a copy of the
output stream.

The pipeline can also be extended dynamically with new pipeline sections with
:meth:`Pipeline.extend() <slurry.Pipeline.extend>`, adding additional processing.

.. autoclass:: slurry.Pipeline
  :members:

Sections
--------

Sections are individual processing steps that can be applied to an asynchronous stream of data. Sections receive input
from the previous section, or from an asynchronous iterable, processes it and sends it to the section output. To use Slurry,
all the user has to do is to configure these sections, and decide on the ordering of each step in the pipeline. The
``Pipeline`` takes care of wiring together sections, so the output gets routed to the input of the subsequent section.

Behind the scenes, data is send between sections using message passing via
`trio memory channels <https://trio.readthedocs.io/en/stable/reference-core.html#using-channels-to-pass-values-between-tasks>`_.
Each section is executed as a
`Trio task <https://trio.readthedocs.io/en/stable/reference-core.html#tasks-let-you-do-multiple-things-at-once>`_
and, from the user perspective, are in principle completely non-blocking and independent of each other.  

Slurry includes a library of ready made sections, with functionality inspired by other reactive frameworks. They
are documented below. For more information about sections, and how to build your own sections, read the :doc:`dev`.

Most ready made sections support an optional source parameter. In most cases this is semantically identical to using that source
as an async interable input to the pipeline, however using the source parameter instead, may sometimes be more readable.

Some sections, like :class:`slurry.sections.Zip`, support multiple inputs, which must be supplied as parameters.

Transforming input
^^^^^^^^^^^^^^^^^^
.. automodule:: slurry.sections._refiners

.. autoclass:: slurry.sections.Map

.. note::
  Although individual sections can be thought of as running independently, this is not a guarantee. Slurry may now, or at any
  later time, chose to apply certain optimizations, like merging a sequence of strictly functional operations
  like :class:`slurry.sections.Map` into a single operation.

Filtering input
^^^^^^^^^^^^^^^
.. automodule:: slurry.sections._filters

.. autoclass:: slurry.sections.Skip

.. autoclass:: slurry.sections.SkipWhile

.. autoclass:: slurry.sections.Filter

.. autoclass:: slurry.sections.Changes

.. autoclass:: slurry.sections.RateLimit


Buffering input
^^^^^^^^^^^^^^^
.. automodule:: slurry.sections._buffers

.. autoclass:: slurry.sections.Window

.. autoclass:: slurry.sections.Group

.. autoclass:: slurry.sections.Delay

Generating new output
^^^^^^^^^^^^^^^^^^^^^
.. automodule:: slurry.sections._producers

.. autoclass:: slurry.sections.Repeat

.. autoclass:: slurry.sections.Metronome

.. autoclass:: slurry.sections.InsertValue

Combining multiple inputs
^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: slurry.sections._combiners

.. autoclass:: slurry.sections.Chain

.. autoclass:: slurry.sections.Merge

.. autoclass:: slurry.sections.Zip

.. autoclass:: slurry.sections.ZipLatest

.. _Node-RED: https://nodered.org/
.. _KNIME: https://www.knime.com/
.. _Alteryx: https://www.alteryx.com/
.. _itertools: https://docs.python.org/3/library/itertools.html
.. _aiostream: https://github.com/vxgmichel/aiostream
.. _eventkit: https://github.com/erdewit/eventkit
.. _asyncitertools: https://github.com/vodik/asyncitertools
.. _Trio: https://trio.readthedocs.io/en/stable/