# History

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