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

Weld
----
.. automodule:: slurry.sections.weld

weld
^^^^
.. autofunction:: slurry.sections.weld.weld

Abc
---
.. automodule:: slurry.sections.abc

Section
^^^^^^^
.. autoclass:: Section
  :members:

AsyncSection
^^^^^^^^^^^^
.. autoclass:: AsyncSection
  :members:

SyncSection
^^^^^^^^^^^
.. autoclass:: SyncSection
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

Threading
---------
.. automodule:: slurry.sections.threading

ThreadSection
^^^^^^^^^^^^^
.. autoclass:: slurry.sections.threading.ThreadSection
  :members:

Multiprocessing
---------------
.. automodule:: slurry.sections.multiprocessing

ProcessSection
^^^^^^^^^^^^^^
.. autoclass:: slurry.sections.multiprocessing.ProcessSection
  :members:
