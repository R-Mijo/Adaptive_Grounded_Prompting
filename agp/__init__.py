"""Adaptive Grounded Prompting reference controls.

This experimental package enforces structural release checks. It does not prove
that cited text supports a claim or authenticate a human approver.
"""

from .core import (
    POLICY_VERSION, REQUIRED_CHECKS, Claim, PAL, Relationship, ReleaseDecision,
    Source, TaskProfile, build_receipt, decide_release, verify_receipt,
)

__version__ = "0.2.0"
__all__ = [
    "POLICY_VERSION", "REQUIRED_CHECKS", "Claim", "PAL", "Relationship",
    "ReleaseDecision", "Source", "TaskProfile", "build_receipt",
    "decide_release", "verify_receipt",
]
