# History

## v0.8.0

* New ProcessSection abc. Code can now be spawned in a seperate python process, making true concurrency possible!
* This is a major refactoring. Lots of files have been moved around. Things will break if you upgrade to this version. More breaking changes are planned for 0.9.0 in order to simplify the api across section types.

## v0.7.0

* New ThreadSection abc. Synchronous python code can now be run transparently next to asynchronous Trio code, using the new ThreadSection class. The pump api is identical to the async version, except that input is a synchronous iterator and the output send function is synchronous function.

## v0.6.0

* Refactored: The tap closure fixes in 0.5.1 didn't entirely hit the mark, triggering a major refactoring of input and output resource management. Additional tests have been added to further strengthen coverage of correct resource management.
* Fixed: The Repeat section could concievably drop items from the input source in certain rare cases. The new implementation guarantees that all input items are send on to the output, while still repeating received items in case of no activity.

## v0.5.1

* Fix early tap closure. If a tap was closed, while items was still waiting to be sent upstream, it would cause an unhandled
BrokenResourceError to be thrown. Now, if all taps are closed, the immediate upstream iterable will be closed, and the pipeline
will stop processing any further items. Any upstream sections will be expected to handle downstream channel closures gracefully.

## v0.5.0

* Per subject rate limiting now allows seperate limiters for different item types depending on a chosen subject.

## v0.4.4

* Fix Group section. Triggering the timeout cancel scope would close the input generator, stopping further output. To fix this, input iteration is now fully decoupled from output generation with a seperate pull task.

## v0.4.3

* Upgrade to trio 0.17

## v0.4.2

* Expose pipeline nursery to end users.

## v0.4.0

* Merge section can now merge other Sections in addition to regular async iterables.

## v0.3.1

* Documentation fixes.

## v0.3.0

* Full API documentation added.
* Some minor refactorings

## v0.2.0

First release to PyPI.