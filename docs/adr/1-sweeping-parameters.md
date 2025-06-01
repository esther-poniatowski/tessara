# ADR 0001: Representation of Sweeping Parameters

**Status**: Proposed

---

## Problem Statement

Currently, individual parameters are represented by the `Param` class, which encapsulates an optional default value and a user-defined runtime value.

This parameter system needs to integrate functionality for "sweeping parameters", allowing systematic exploration of a range of values in workflows.

**Questions to be addressed**:

1. Should sweeping parameters be represented as an extension of `Param` or as a separate subclass?

---

## Decision Drivers

- **Consistency**: Sweeping parameters should behave consistently with other parameters to limit
  special cases in handling them (e.g., in the `ParameterSet` class).
- **No Duplication (DRY)**: Avoid redundant code for sweeping parameters, as most of their behavior
  is already defined in the `Param` class.
- **Complexity**: Implement a lightweight and simple solution for representing sweeping parameters.
- **Modularity**: Encapsulate sweeping functionality without cluttering the core parameter logic.
- **Separation of Concerns**: Clearly delineate sweeping behavior from standard parameter
  operations.
- **Extensibility**: Allow future enhancements without breaking the existing API.
- **Usability**: Provide an intuitive API for defining and interacting with sweeping parameters.

---

## Considered Options

### 1. Extending `Param` with Sweeping Attributes

This approach integrates sweeping-related attributes directly into the `Param` class.

- Adds an optional `is_sweep: bool` flag.
- Introduces a `values: Optional[List[Any]]` attribute to store sweep values.
- Methods such as `get_values()` return either a single value (if `is_sweep=False`) or the sweep
  values (if `is_sweep=True`).

```python
class Param:
    def __init__(self, default=None, values: Optional[List[Any]] = None, is_sweep: bool = False):
        self.default = default
        self.values = values if values else [default]
        self.is_sweep = is_sweep

    def get_values(self) -> List[Any]:
        return self.values if self.is_sweep else [self.default]
```

### 2. Creating a Dedicated `ParamGrid` Subclass

This approach introduces a separate `ParamGrid` class that extends `Param` and specializes in sweeping behavior.

- Encapsulates sweeping-specific logic within `ParamGrid`.
- Inherits from the `Param` class to reuse common parameter functionality.
- Overrides methods such as `get_values()` to accommodate sweeping behavior.

```python
class ParamGrid(Param):
    def __init__(self, values: List[Any]):
        super().__init__(default=values[0])
        self.values = values

    def get_values(self) -> List[Any]:
        return self.values
```

---

## Analysis of Options

### Individual Assessment

#### **1. Extending `Param` with Sweeping Attributes**

*Pros:*

- **Consistency**: Maintains a single `Param` class, simplifying type handling across the codebase.
- **No Duplication (DRY)**: Avoids creating an additional class, keeping logic centralized.
- **Complexity**: Introduces minimal additional logic to the existing class.

*Cons:*

- **Separation of Concerns**: Embeds sweeping logic into a general-purpose class, making it less
  focused.
- **Extensibility**: If more sophisticated sweeping behavior is needed later, modifying `Param`
  could lead to unnecessary complexity.

#### **2. Creating a Dedicated `ParamGrid` Subclass**

*Pros:*

- **Separation of Concerns**: Clearly isolates sweeping functionality from standard parameter
  behavior.
- **Extensibility**: Provides a dedicated class that can evolve independently as sweeping needs
  grow.
- **Modularity**: Maintains `Param` as a general-purpose class while adding specialization through
  inheritance.

*Cons:*

- **Consistency**: Introduces a separate class, requiring additional handling in cases where both
  `Param` and `ParamGrid` interact.
- **Complexity**: Adds another class to the system, though the added complexity is minimal.

### Summary: Comparison by Criteria

- **Consistency**
  - **Extending `Param`**: High (single class, fewer type distinctions).
  - **Dedicated `ParamGrid`**: Medium (introduces a separate class).

- **No Duplication (DRY)**
  - **Extending `Param`**: High (no redundant code).
  - **Dedicated `ParamGrid`**: Medium (inherits but introduces additional logic).

- **Complexity**
  - **Extending `Param`**: Low (minimal changes to an existing class).
  - **Dedicated `ParamGrid`**: Medium (additional class but clearer separation).

- **Separation of Concerns**
  - **Extending `Param`**: Low (mixes concerns within a single class).
  - **Dedicated `ParamGrid`**: High (clear distinction between standard and sweeping parameters).

- **Extensibility**
  - **Extending `Param`**: Medium (future modifications may complicate `Param`).
  - **Dedicated `ParamGrid`**: High (isolates changes to sweeping behavior).

---

## Conclusions

### Decision

**Chosen option**: Creating a dedicated `ParamGrid` subclass.

**Justification**: This approach provides a clear separation of concerns while maintaining modularity and extensibility. The `ParamGrid` class allows future enhancements related to sweeping behavior without impacting the core `Param` class.

**Discarded option**:

- **Extending `Param`**: Embeds sweeping logic within a general-purpose class, reducing separation of concerns and making future extensions less manageable.

### Final Answers

1. **Should sweeping parameters be represented as an extension of `Param` or as a separate subclass?**
   - A separate subclass (`ParamGrid`) provides better separation of concerns and allows easier future modifications without affecting the core parameter class.

---

## Implications

- **Modification of `ParameterSet`**: The `ParameterSet` class must be updated to handle
  `ParamGrid` correctly, ensuring it supports both standard and sweeping parameters.
- **Refactoring of Type Handling**: Functions that process parameters need to account for
  `ParamGrid` explicitly.
- **Future Extension Possibilities**: If required, `ParamGrid` can later include additional methods
  for advanced sweeping strategies (e.g., logarithmic scaling, grid search).

---

## See Also

### References and Resources

- [Design Patterns: Inheritance vs. Composition](https://martinfowler.com/articles/inheritance-vs-composition.html)
- [Encapsulation and Object-Oriented Design Principles](https://www.oreilly.com/library/view/design-patterns-elements/0201633612/)
