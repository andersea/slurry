===
API
===

Pipeline
--------
.. automodule:: slurry.pipeline

Pipeline
^^^^^^^^
.. autoclass:: Pipeline
  :members:

Abc
---
.. automodule:: slurry.sections.abc

PipelineSection
^^^^^^^^^^^^^^^

A ``PipelineSection`` is any object that is valid in the definition of a new a :class:`Pipeline` process.
This currently includes the following types:

* ``AsyncIterable[Any]`` - Async iterables are valid only as the very first ``PipelineSection``. Subsequent
  sections will use this async iterable as input source.
* A :class:`Section`, :class:`ThreadSection` or :class:`ProcessSection`
* ``Tuple[PipelineSection, ...]`` - Pipeline sections can be nested to any level by supplying a tuple
  containing one or more PipelineSections. Output from upstream sections are automatically used as input
  to the nested sequence of pipeline sections.

Section
^^^^^^^
.. autoclass:: Section
  :members:

ThreadSection
^^^^^^^^^^^^^
.. autoclass:: ThreadSection
  :members:

ProcessSection
^^^^^^^^^^^^^^
.. autoclass:: ProcessSection
  :members:

Weld
----
.. automodule:: slurry.sections.weld
  :members:

Pump
----
.. automodule:: slurry.sections.pump
  :members:

Buffers
-------
.. automodule:: slurry.sections._buffers

Window
^^^^^^
.. autoclass:: slurry.sections.Window

Group
^^^^^
.. autoclass:: slurry.sections.Group

Delay
^^^^^
.. autoclass:: slurry.sections.Delay

Combiners
---------
.. automodule:: slurry.sections._combiners

Chain
^^^^^
.. autoclass:: slurry.sections.Chain

Merge
^^^^^
.. autoclass:: slurry.sections.Merge

Zip
^^^
.. autoclass:: slurry.sections.Zip

ZipLatest
^^^^^^^^^
.. autoclass:: slurry.sections.ZipLatest

Filters
-------
.. automodule:: slurry.sections._filters

Skip
^^^^
.. autoclass:: slurry.sections.Skip

Filter
^^^^^^
.. autoclass:: slurry.sections.Filter

Changes
^^^^^^^
.. autoclass:: slurry.sections.Changes

RateLimit
^^^^^^^^^
.. autoclass:: slurry.sections.RateLimit


Producers
---------
.. automodule:: slurry.sections._producers

Repeat
^^^^^^
.. autoclass:: slurry.sections.Repeat


Refiners
--------
.. automodule:: slurry.sections._refiners

Map
^^^
.. autoclass:: slurry.sections.Map

