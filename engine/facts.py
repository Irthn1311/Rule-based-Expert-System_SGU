"""
Facts Module
Defines the Experta Fact classes used by the diagnosis engine.
"""

from experta import Fact, Field


class Symptom(Fact):
    """
    Represents a single symptom observation.
    
    Attributes:
        code: The symptom code (e.g., 'power_response')
        value: Boolean value (True/False) indicating presence of symptom
    """
    code = Field(str, mandatory=True)
    value = Field(bool, mandatory=True)


class DiagnosisResult(Fact):
    """
    Represents the diagnosis result produced by the inference engine.
    
    Attributes:
        rule_id: The ID of the matched rule
        cause: The diagnosed cause
        solution: The recommended solution
        priority: Priority of the matched rule
    """
    rule_id = Field(str, mandatory=True)
    cause = Field(str, mandatory=True)
    solution = Field(str, mandatory=True)
    priority = Field(int, default=0)
