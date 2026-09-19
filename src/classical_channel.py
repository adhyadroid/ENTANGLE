"""
classical_channel.py, ENTANGLE

Replay cannot happen on the quantum channel (measurement destroys the
state, no-cloning). What can be replayed is the classical announcement
(Alice's Bell-measurement bits + basis + a session tag). This module binds
every round to a monotonic counter and detects reuse deterministically, no statistics, no learned threshold.
"""

import hashlib
from dataclasses import dataclass


@dataclass
class Transcript:
    round_id: int
    nonce: str
    classical_bits: tuple
    basis: str
    tag: str


class ClassicalChannel:
    def __init__(self):
        self._seen_tags = set()
        self._last_round_id = -1

    @staticmethod
    def _make_tag(round_id: int, nonce: str, bits: tuple, basis: str) -> str:
        payload = f"{round_id}|{nonce}|{bits}|{basis}".encode()
        return hashlib.sha256(payload).hexdigest()

    def send(self, round_id: int, bits: tuple, basis: str, nonce: str) -> Transcript:
        tag = self._make_tag(round_id, nonce, bits, basis)
        return Transcript(round_id, nonce, bits, basis, tag)

    def receive(self, transcript: Transcript) -> bool:
        """Return True if the transcript is accepted (fresh, monotonic), False if replay."""
        expected_tag = self._make_tag(
            transcript.round_id, transcript.nonce, transcript.classical_bits, transcript.basis
        )
        if expected_tag != transcript.tag:
            return False  # tampered transcript
        if transcript.round_id <= self._last_round_id:
            return False  # stale/replayed round id
        if transcript.tag in self._seen_tags:
            return False  # exact tag reuse
        self._seen_tags.add(transcript.tag)
        self._last_round_id = transcript.round_id
        return True


# ---------------------------------------------------------------------------
# PHASE 2 (diagnostic / non-gating addition): classical channel authentication
# ---------------------------------------------------------------------------
# This does NOT replace ClassicalChannel's replay defense above, and it does
# NOT feed the SPRT/symmetrization security decision. It answers a different
# question: was THIS specific classical message tampered with in transit
# (a MITM on basis reconciliation), as opposed to "was this transcript seen
# before" (replay). docs/limitations.md documents why the channel is
# otherwise unauthenticated; this is a minimal demonstration of what closing
# that gap would look like, a single lightweight universal-hash MAC
# function, not a full Wegman-Carter protocol suite.

_PRIME = 2_305_843_009_213_693_951  # a Mersenne prime, large enough for this demo


class WegmanCarterMAC:
    """Simplified universal-hash MAC: mac(m) = (a*m + b) mod p.
    In real Wegman-Carter, (a,b) must be used only once per message to keep
    the information-theoretic security guarantee; this demo reuses one key
    per ClassicalChannel session for simplicity, a scope simplification,
    not the full protocol, exactly as docs/limitations.md states."""

    def __init__(self, rng: "random.Random" = None):
        import random
        rng = rng or random.Random()
        self.a = rng.randrange(1, _PRIME)
        self.b = rng.randrange(0, _PRIME)

    def _to_int(self, transcript: Transcript) -> int:
        payload = f"{transcript.round_id}|{transcript.nonce}|{transcript.classical_bits}|{transcript.basis}".encode()
        return int(hashlib.sha256(payload).hexdigest(), 16) % _PRIME

    def tag_for(self, transcript: Transcript) -> int:
        return (self.a * self._to_int(transcript) + self.b) % _PRIME

    def verify(self, transcript: Transcript, presented_mac: int) -> bool:
        return self.tag_for(transcript) == presented_mac
