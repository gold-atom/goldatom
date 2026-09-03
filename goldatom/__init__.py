"""GoldAtom/0 — experimental Proof-Buried Work prototype."""

from .models import GoldAtomBundle
from .verify import VerificationError, VerificationReport, verify_bundle

__all__ = [
    "GoldAtomBundle",
    "VerificationError",
    "VerificationReport",
    "verify_bundle",
]

__version__ = "0.0.3"
