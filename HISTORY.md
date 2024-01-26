# History

## v1.3.2

A lot of quality of life improvements, curtesy of Mike Nerone [@mikenerone](https://github.com/mikenerone).

* Add support for python 3.11 and 3.12
* Updated dependencies
* Various build fixes for github actions and readthedocs
* Improved typings across the board
* Fix unsafe use of iterables
* Metronome test speedup with timer mocking
* Allow InsertValue to be used as first section.

## v1.3.1

* Add support for python 3.10, remove support for python 3.7.
* Bump trio to 0.21.0
* Minor documentation fixes.

## v1.2.0

* Added Metronome, which is a repeater section similar to Repeat, however the timing is based on the wall clock and
receiving new items doesn't reset the timer.
* Added InsertValue, which sends a single item once, and then passes through any received items unmodified.
* Updated all dependencies.
* Support for python 3.10 was intended for this version, but tests are failing at the moment, due to a build issue.
Therefore 3.10 support is postponed for now.

## v1.1.1

* Added SkipWhile section, which skips items until a predicate evaluates to false.
* Update all dependencies. Minimum python version bumped to 3.7.

## v1.0.0

* Documentation has been further reworked and refined. As this version is feature complete for my personal use, and
has good documentation, we are good to release as v1.0.

## v0.10.4

* Update to trio 0.18

## v0.10.3

* Fix unhandled StopAsyncIteration in Skip section.

## v0.10.2

* Switch to github actions for CI.
* Minor documentation edits.

## v0.10.1

* Thorough api documentation rework.

## v0.10.0

(Not released.)

* Introducing external environments. Via the new AsyncSection and SyncSection base classes, it is now
possible to create custom environments to run sections in. In v0.7.0 and v0.8.0, ThreadSection and
ProcessSection was introduced. The environments that ran these sections was hardcoded into the Pipeline
machinery. With this change, the Section itself is responsible for setting up the environment it runs in.
This means, that external sections can now create and manage their environments, and data should flow
between those environments and the main pipeline transparently.
* Api change: Introduces the refine method. The actual work that the pipeline section performs should be
done here.

## v0.9.0

* New PipelineSection concept. The pipeline section generalizes the types of input that is allowed in pipelines and select sections that take input. PipelineSection objects can either be asynchronous iterables, Sections or Tuples representing sequences of pipeline sections. Using tuples of pipeline sections, it possible to compose nested pipelines to any depth.
* Changed api. Section pumps now take a callable that returns an awaitable as output, instead of an explicit trio.MemorySendChannel. This brings the api in line with synchronous sections, however this is obviously a breaking change.

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