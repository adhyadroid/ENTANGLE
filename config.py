"""config.py, ENTANGLE. Central place for tunable protocol parameters."""

MAX_ROUNDS = 400
ALPHA = 0.01                    # target false-positive rate (reject an honest signature)
BETA = 0.01                     # target false-negative rate (accept a forged signature)
ATTACK_MARGIN = 0.15            # p1 = p0 + margin, absent an attack-specific rate
EXPECTED_CHANNEL_NOISE = 0.05   # simulated physical bit-flip noise, present with no attacker
CALIBRATION_ROUNDS = 120
