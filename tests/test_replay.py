"""tests/test_replay.py"""
from classical_channel import ClassicalChannel


def test_honest_transcript_accepted():
    ch = ClassicalChannel()
    t = ch.send(round_id=1, bits=(0, 1), basis="Z", nonce="n1")
    assert ch.receive(t) is True


def test_exact_replay_rejected():
    ch = ClassicalChannel()
    t = ch.send(round_id=1, bits=(0, 1), basis="Z", nonce="n1")
    assert ch.receive(t) is True
    replay = ch.send(round_id=1, bits=(0, 1), basis="Z", nonce="n1")
    assert ch.receive(replay) is False


def test_stale_round_id_rejected_even_with_new_nonce():
    ch = ClassicalChannel()
    ch.receive(ch.send(round_id=5, bits=(1, 0), basis="X", nonce="n5"))
    stale = ch.send(round_id=3, bits=(1, 1), basis="Z", nonce="n_different")
    assert ch.receive(stale) is False


def test_tampered_tag_rejected():
    ch = ClassicalChannel()
    t = ch.send(round_id=1, bits=(0, 1), basis="Z", nonce="n1")
    t.tag = "0" * 64  # tamper
    assert ch.receive(t) is False


def test_monotonic_counter_advances():
    ch = ClassicalChannel()
    ch.receive(ch.send(round_id=1, bits=(0, 0), basis="Z", nonce="a"))
    ch.receive(ch.send(round_id=2, bits=(0, 1), basis="Z", nonce="b"))
    assert ch._last_round_id == 2
