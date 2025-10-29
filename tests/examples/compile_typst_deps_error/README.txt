This example illustrates an error that is not handled well (at the time of writing).
When typst loads an input file that exists but breaks the compilation,
it will not write a dep file, and StepUp RepRep can therefore not know
that it should reschedule the typspt compilation after the input has been updated.

This illustration keeps things simple by starting StepUp
with a broken version of the input, as if it lingers from a previous build.
