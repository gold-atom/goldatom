"""Named protocol profiles.

No mainnet profile exists in version zero. That omission is deliberate.
"""

from __future__ import annotations

from dataclasses import dataclass


ALGORITHM_SHA256D_80_V0 = "sha256d-80-v0"


@dataclass(frozen=True, slots=True)
class ProtocolProfile:
    id: str
    network: str
    challenge_delay: int
    mint_window: int
    maximum_target: int
    minimum_burial_blocks: int
    minimum_burial_chainwork: int

    @property
    def maximum_target_hex(self) -> str:
        return f"{self.maximum_target:064x}"


# Deliberately easy: about 16 hashes of expected work at the maximum target.
# This profile exists only to make tests and local demonstrations fast.
_SIM_MAX_TARGET = (1 << 252) - 1

PROFILES: dict[str, ProtocolProfile] = {
    "goldatom-sim-v0": ProtocolProfile(
        id="goldatom-sim-v0",
        network="simnet",
        challenge_delay=3,
        mint_window=12,
        maximum_target=_SIM_MAX_TARGET,
        minimum_burial_blocks=1,
        minimum_burial_chainwork=1,
    ),
    "goldatom-regtest-v0": ProtocolProfile(
        id="goldatom-regtest-v0",
        network="regtest",
        challenge_delay=3,
        mint_window=12,
        maximum_target=_SIM_MAX_TARGET,
        minimum_burial_blocks=1,
        minimum_burial_chainwork=1,
    ),
}


def get_profile(profile_id: str) -> ProtocolProfile:
    try:
        return PROFILES[profile_id]
    except KeyError as exc:
        known = ", ".join(sorted(PROFILES))
        raise ValueError(f"unknown GoldAtom profile {profile_id!r}; known profiles: {known}") from exc
