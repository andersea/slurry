===
API
===

Pipeline
--------
.. automodule:: slurry._pipeline

.. autoclass:: slurry.Pipeline
  :members:

Sections
--------

Transforming input
^^^^^^^^^^^^^^^^^^
.. automodule:: slurry.sections._refiners

.. autoclass:: slurry.sections.Map


Filtering input
^^^^^^^^^^^^^^^
.. automodule:: slurry.sections._filters

.. autoclass:: slurry.sections.Skip

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

Combining multiple inputs
^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: slurry.sections._combiners

.. autoclass:: slurry.sections.Chain

.. autoclass:: slurry.sections.Merge

.. autoclass:: slurry.sections.Zip

.. autoclass:: slurry.sections.ZipLatest

Abstract base classes
^^^^^^^^^^^^^^^^^^^^^
.. automodule:: slurry.sections.abc

.. autoclass:: Section
  :members:

.. autoclass:: AsyncSection
  :members:

.. autoclass:: SyncSection
  :members:

Welding sections
^^^^^^^^^^^^^^^^
.. automodule:: slurry.sections.weld
  :members:

Environments
------------

Environments are implementations of :class:`AsyncSection <slurry.sections.abc.AsyncSection>` or
:class:`SyncSection <slurry.sections.abc.SyncSection>`, that is, they have a pump method
implementation that can run the section's ``refine`` method in derived classes.

Trio
^^^^
.. automodule:: slurry.environments._trio

.. autoclass:: slurry.environments.TrioSection
  :members:


Threading
^^^^^^^^^
.. automodule:: slurry.environments._threading

.. autoclass:: slurry.environments.ThreadSection
  :members:


Multiprocessing
^^^^^^^^^^^^^^
.. automodule:: slurry.environments._multiprocessing

.. autoclass:: slurry.environments.ProcessSection
  :members:
