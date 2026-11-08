# TODO

Items are grouped by the condition that opens them.

## Defects observed against the layout of project repositories

The assessment of 2026-11-08 checked Tessara against the common layout of the project repositories of Geonexus. Tessara fits that layout, since it reads only the files whose paths its caller gives. The following defects of Tessara itself would harm a project that uses it, or Meandra, which adapts it.

- [ ] **Export the public classes.** `src/tessara/__init__.py` exports only `info` and `__version__`. The quick start of the README therefore fails at `from tessara import ParamSet, Param`, and Meandra cannot resolve `ParameterSet` and `ParamSweeper` for its type checks and its doctests. Export `Param`, `ParameterSet`, `ParamGrid` and `ParamSweeper`, and align the quick start with the actual signature of `Param`, which takes no `bounds` or `type`.
- [ ] **Write a parameter set to YAML.** The README announces saving to YAML, but the source holds no writer. Add the writer, and let it write the resolved values of a run, which a project keeps as a run record beside the data of that run.
- [ ] **Test the validation.** `tests/test_tessara/test_validation/` holds only `__init__.py`, so the rules of `src/tessara/validation/` have no test.
- [ ] **Complete the documentation.** `docs/internals/` is empty, the first ADR still reads "Proposed" although `ParamGrid` exists, and the README links to a `CITATION.cff` that the repository does not hold.
