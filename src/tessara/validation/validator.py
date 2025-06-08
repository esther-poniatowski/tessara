"""
tessara.validation.validator
============================

Validation of parameters and parameter sets.

TODO: Would a logging system be useful to track the validation process instead of the "handmade" report?


Classes
-------
ReportEntry
    Representation of a single validation report entry.
Check
    Specification of a single validation check.
Validator
    Validate input values against a set of rules.

Notes
-----
Individual rules can already validate values by themselves, which allows for testing in isolation.
The Validator class is a higher-level component that aggregates the outcomes of multiple rules.
"""
from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Any, List, Dict, Optional, TypeAlias
from collections.abc import Iterable, Mapping

from tessara.validation.rules import Rule
from tessara.errors.validation import GlobalValidationError, ValidationError, CheckError
from tessara.core.parameters import ParameterSet


Targets : TypeAlias = Iterable[str] | Mapping[str, str]
"""Type alias for target parameters (names) to validate."""
Values : TypeAlias = List[Any] | Dict[str, Any]
"""Type alias for values to validate against a rule, retrieved from the target names."""


# --- Event Tacking --------------------------------------------------------------------------------

@dataclass
class ReportEntry:
    """
    Representation of a single validation report entry.

    Attributes
    ----------
    rule : str
        Name of the rule that was checked.
    targets : Targets
        Specification of the parameter(s) to validate, by their names in the ParameterSet instance.
    success : bool
        Outcome of the validation process.
        If True, the check passed successfully.
        If False, the check failed.
        If None, the check could not complete (e.g. error in rule execution).
    message : str
        Error message if the validation failed.
    """
    rule: str
    targets: Targets
    success: Optional[bool] = None
    message: str = ""


class ValidationRecorder:
    """
    Handle validation reports and error aggregation separately from validation execution.

    Attributes
    ----------
    report : List[ReportEntry]
        Report of the validation process, aggregating outcomes across checks.
    errors : List[ValidationError]
        Stack of errors collected across all checks (validation and execution errors).

    See Also
    --------
    ReportEntry
        Representation of a single validation report entry.
    ValidationError
        Base class for all validation errors.
    Rule.get_error(*args, **kwargs) -> ValidationError | None
        Method to generate the output of a rule check.
    """
    SUCCESS_FLAG = "PASSED"

    def __init__(self):
        self.report: List[ReportEntry] = []
        self.errors: List[ValidationError] = []

    def record(self, rule: Rule, targets: Targets, error: Optional[ValidationError | CheckError] = None) -> None:
        """
        Register a validation check in the report.

        Arguments
        ---------
        rule, targets
            See the corresponding attributes in the Check class.
        error : ValidationError | CheckError | None
            Error object if the validation check failed.
            If None, the check passed successfully.
        """
        success = error is None
        if not success:
            self.errors.append(error) # collect error
            message = error.message # get message from error
        else:
            message = self.SUCCESS_FLAG # default message if no error
        self.report.append(ReportEntry(rule.__class__.__name__, targets, success, message))

    def get_report(self) -> List[ReportEntry]:
        """Retrieve the complete validation report."""
        return self.report

    def get_errors(self) -> List[ValidationError]:
        """Retrieve only errors."""
        return self.errors

    def has_errors(self) -> bool:
        """Signal if any errors occurred."""
        return bool(self.errors)


# --- Validation Process ---------------------------------------------------------------------------

class Checker:
    """
    Specifies and performs a single validation check on a ParameterSet.

    This layer serves to standardize the inputs and outputs of the validation process, so that they
    do not depend on the type of rule being checked (parameter-specific or relational).

    Attributes
    ----------
    rule : Rule
        Rule to apply (instance of the Rule subclass).
    targets : Targets
        Specification of the parameter(s) to validate by their names in the ParameterSet instance.

    Methods
    -------
    bind_targets(params: ParameterSet) -> Values
        Retrieve the target values from the ParameterSet instance.
    check(params: ParameterSet) -> ValidationError | None
        Perform a single check of input values against a rule.
    """
    ARGS_MODE = "args"
    KWARGS_MODE = "kwargs"

    def __init__(self, rule: Rule, targets: Targets) -> None:
        self.rule = rule
        if isinstance(targets, Mapping):
            self.argument_mode = self.KWARGS_MODE
            self.targets = dict(targets)
        elif isinstance(targets, Iterable):
            self.argument_mode = self.ARGS_MODE
            self.targets = tuple(targets)
        else:
            raise TypeError(f"Expected targets to be Iterable or Mapping, got {type(targets).__name__}.")

    def bind_targets(self, params: ParameterSet) -> Values:
        """
        Retrieve target values from the ParameterSet instance.

        Arguments
        ---------
        param : ParameterSet
            Set of parameters to validate, containing Param instances named as the targets.

        Returns
        -------
        Values
            Values of the parameters to validate, depending on the type of the targets.
            If the target are specified in a list of parameter names, the method returns a list of
            values in the same order.
            If the targets are specified in a dictionary, the method returns a dictionary of values
            with the same keys.
        """
        if self.argument_mode == self.ARGS_MODE: # `args` mode
            return [params[name].value for name in self.targets]
        return {name: params[name].value for name in self.targets} # `kwargs` mode

    def check(self, params: ParameterSet) -> ValidationError | None:
        """
        Perform a single check of input values against a rule.

        Arguments
        ---------
        params : ParameterSet
            Set of parameters to validate, containing Param instances named as the targets.

        Returns
        -------
        error : ValidationError | None
            If the check fails, it provides an error summarizing the failure.
            If the check passes, it returns None.

        See Also
        --------
        Rule.get_error(*args, **kwargs) -> ValidationError | None
            Method to generate the output of a rule check.
        """
        values = self.bind_targets(params)
        if self.argument_mode == self.ARGS_MODE: # `args` mode
            return self.rule.get_error(*values)
        return self.rule.get_error(**values)  # `kwargs` mode

class Validator(ABC):
    """
    Validate input values against a set of rules.

    Input values are fixed while several rules can be checked against them.

    Class Attributes
    ----------------
    SUCCESS_FLAG : str
        Default message indicating that a check passed during the validation process.

    Attributes
    ----------
    params : ParameterSet
        Set of parameters to validate.
    strict : bool
        Flag to enable strict mode, which determines the severity of the checks.
        In strict mode, the any rule failure will raise a GlobalValidationError at the end of the
        validation process.
        In non-strict mode, the validation simply collects all errors in the report.

    Methods
    -------
    reset_checks() -> None
        Reset the checks to perform on the parameters during a new validation process.
    reset_outcomes() -> None
        Reset the error stack and the report for a new validation process.
    filter(include_only, exclude) -> List[Check]
        Filter the checks to perform on the parameters based on the rule type.
    validate() -> bool
        Execute the full validation process over a set of parameters and rules.

    See Also
    --------
    ParameterSet
        Set of parameters to validate, with individual rules and relationships.
    Param
        Single parameter to validate, nested in a ParameterSet instance.
    Rule
        Base class for validation rules to apply.
    ValidationError
        Base class for all validation errors.
    Check
        Representation of a single validation check.
    """
    def __init__(self, params: ParameterSet, strict: bool = False) -> None:
        self.params = params
        self.strict = strict
        self.recorder = ValidationRecorder()
        self.checks: List[Checker] = []

    def init_checks(self) -> None:
        """
        Determine all the checks to perform on the parameters during a new validation process.

        Checks are dynamically generated based on the rules associated with the parameters:

        1. Check type and constraints of individual parameters (parameter-specific rules).
        2. Check relationships between parameters (global rules).

        Returns
        -------
        List[Check]
            Checks to perform on the parameters, before any filtering.
        """
        checks = []
        for name, param in self.params.items(): # all Param instances in the set
            for rule in param.rules: # one check per rule for each parameter
                checks.append(Checker(rule, targets=[name]))
        for rule, targets in self.params.relation_rules: # all global rules in the set
            checks.append(Checker(rule, targets))
        return checks

    @staticmethod
    def filter(checks : List[Checker],
               include_only: Optional[Iterable[Rule]] = None,
               exclude: Optional[Iterable[Rule]] = None
               ) -> List[Checker]:
        """
        Filter the checks to perform on the parameters based on the rule type.

        Arguments
        ---------
        checks : List[Check]
            Checks to filter based on the rule type.
        include_only : Iterable[Rule]
            Rule types to include exclusively in the checks. It takes precedence over the `exclude`
            argument if both are provided.
        exclude : Iterable[Rule]
            Rule types to exclude from the checks, if the `only` argument is not provided.
        """
        if include_only:
            return [chk for chk in checks if chk.rule in include_only]
        if exclude:
            return [chk for chk in checks if chk.rule not in exclude]
        return checks

    def validate(self,
                 include_only: Optional[Iterable[Rule]] = None,
                 exclude: Optional[Iterable[Rule]] = None
                 ) -> bool:
        """
        Execute the full validation process over a set of parameters and rules.

        1. Reset the report to start a new validation process on new values.
        2. Iterate over the checks to perform.
        3. Retrieve the target values from the ParameterSet instance.
        4. Execute the rule on the target values and catch the outcome.
        5. Aggregate the outcomes of the rules in the report and the error stack.
        6. Determine the global validation status (True if all rules passed).

        Returns
        -------
        bool
            True if all rules pass, False otherwise.

        Raises
        ------
        Exception
            If a rule itself fails to execute (before returning its outcome).
        """
        # Start a new validation process
        self.recorder.report.clear()
        self.recorder.errors.clear()
        self.checks = self.init_checks()
        if include_only or exclude:
            checks = self.filter(checks, include_only, exclude)
        # Iterate over the checks
        for chk in checks:
            rule, targets = chk.rule, chk.targets
            try: # catch rule outcomes
                values = chk.bind_targets(self.params) # retrieve target values
                error = self.check(rule, values) # ValidationError or None
            except Exception as exc: # catch execution errors (no rule outcome)
                error = CheckError(exc)
            # Record the outcome of the check
            self.recorder.record(rule, targets, error)
        valid = not self.recorder.has_errors()
        if self.strict and not valid:
            raise GlobalValidationError(self.recorder.get_errors())
        return valid
