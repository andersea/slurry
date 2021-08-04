===============
Developer Guide
===============

Introduction
------------

This part of the documentation describes how to write your own custom section. In most cases, this entails deriving
from :class:`slurry.environments.TrioSection` and implementing the :meth:`slurry.sections.abc.AsyncSection.refine`
method from the AsyncSection abc::

  class Squares(TrioSection):
      async def refine(self, input, output):
          async for i in input:
              await output(i*i)

Slurry is supports two basic types of sections, defined as abstract base classes,
:class:`SyncSection <slurry.sections.abc.SyncSection>` and :class:`AsyncSection <slurry.sections.abc.AsyncSection>`.
Both types of sections define a ``refine`` method, which, when implemented, does the actual processing for the section.

Abstract Base Classes
---------------------

AsyncSection
^^^^^^^^^^^^

Since Slurry is natively an async framework, we will look at this first.

.. autoclass:: slurry.sections.abc.AsyncSection
  :members:

The default :class:`TrioSection <slurry.environments.TrioSection>` environment, is an implementation of 
:class:`AsyncSection <slurry.sections.abc.AsyncSection>`.

SyncSection
^^^^^^^^^^^

Slurry also supports sections that run synchonously. Synchronous and asynchonous sections can be freely mixed and
matched in the pipeline.

.. autoclass:: slurry.sections.abc.SyncSection
  :members:

Slurry includes two implementations of :class:`SyncSection <slurry.sections.abc.SyncSection>`.
:class:`ThreadSection <slurry.environments.ThreadSection>`, which runs the refine function in
a background thread, and :class:`ProcessSection <slurry.environments.ProcessSection>`
which spawns an independent process that runs the refine method.

Section
^^^^^^^

Implementations of :class:`AsyncSection <slurry.sections.abc.AsyncSection>` and
:class:`SyncSection <slurry.sections.abc.SyncSection>`, are refered to as `Environments`_.
Environments implements the :meth:`pump() <slurry.sections.abc.Section.pump>` method of the
:class:`Section <slurry.sections.abc.Section>` abstract base class, which acts as a bridge
between the native event loop and the :class:`AsyncSection <slurry.sections.abc.AsyncSection>` or
:class:`SyncSection <slurry.sections.abc.SyncSection>` ``refine`` method. 

The :meth:`pump() <slurry.sections.abc.Section.pump>` abstract method, is scheduled to run as a task
in the native Trio event loop by the pipeline.
The pump method serves as an underlying machinery for pulling and pushing data through the section.

.. autoclass:: slurry.sections.abc.Section
  :members:

By default, the pipeline tries to manage the input and output resource lifetime. Normally
you don't have to worry about closing the input and output after use. The exception is, if
your custom section adds additional input sources, or provides it's own input. In this case
the section must take care of closing the input after use.

.. note::
  The receiving end of the output can be closed by the pipeline, or by the downstream
  section, at any time. If you try to send an item to an output that has a closed receiver,
  a ``BrokenResourceError`` will be raised. The pipeline knows about this and is prepared
  to handle it for you, but if you need to do some kind of cleanup, like closing network
  connections for instance, you may want to handle this exception yourself.

Although custom sections `should` implement either the :class:`AsyncSection <slurry.sections.abc.AsyncSection>` or
:class:`SyncSection <slurry.sections.abc.SyncSection>` ``refine`` api, this is not strictly a requirement but rather more
like a convention. Any class that implements the :class:`Section <slurry.sections.abc.Section>` abc is
technically a valid pipeline section and can be used in a pipeline.

Environments
------------

Slurry comes with a set of premade environments, suited for both asynchronous and synchronous processing.
As stated earlier, sections can be freely mixed and matched in the pipeline. The section implementation should
be designed so that bridging between the synchronous and asynchronous world happens transparently to the end user,
without blocking the underlying event loop.

When implementing an environment the following rule should be adhered to, if possible. Both the
inputs and the output should be treated as being attached to a zero length buffer. What this means
is that the output of the previous section, should block, until the input has been received on
the next section. This is the default behaviour of zero capacity trio memory channels. The same
behaviour can be achieved using regular queues, by joining the queue after putting an item into it,
and waiting for the remote end to call task_done. Any environment that deviates from this behaviour
should note so, in it's documentation.

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
^^^^^^^^^^^^^^^
.. automodule:: slurry.environments._multiprocessing

.. autoclass:: slurry.environments.ProcessSection
  :members:

Welding sections together
-------------------------

The weld module implements the ``weld`` function that connects ``PipelineSection`` objects 
together and returns the async iterable output.

The ``weld`` function could be considered the secret sauce
of Slurry. The main idea behind Slurry is to have a series of asynchronous, independent tasks, communicating
via memory channels. Setting up tasks for data processing and supplying them with communication infrastructure
can quickly become quite repetitive when using vanilla Trio code. This is where the ``weld`` function comes in.
It automatically takes care of all the boilerplate of feeding inputs to sections, connecting sections via memory
channels and returning the output. This means the programmer can focus on designing the actual dataprocessing steps,
and not having to worry about building message passing infrastructure.

The main :class:`Pipeline <slurry.Pipeline>` class uses the ``weld`` function to compose the sequence of
``PipelineSection`` objects and return an output. Similarly, the
:ref:`combiner sections <user:Combining multiple inputs>` use the ``weld`` function to support defining
sub-pipelines as input sources, using the tuple notation. User defined
custom sections, can also use the ``weld`` funcion to add the same functionality.

.. autofunction:: slurry.sections.weld.weld
