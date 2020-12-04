# History

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