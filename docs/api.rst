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

