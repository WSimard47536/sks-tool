---
type: requirements
title: Data logger requirements
description: Example requirements for a fictional flight data logger; replace them with your own.
---

<!-- What the project must satisfy; if one is not met, the project misses its
     objectives, does not work, or is unsafe. -->

## LOG-001

Type: Business

Status: Underway

The logger **shall** record the flight data needed for post-flight vibration analysis.

- Rationale: Vibration analysis is how the airframe team confirms the structure stays within its limits.

Acceptance criteria:

- [x] A bench recording holds every channel the vibration analysis uses.
- [ ] The airframe team accepts a flight log as input to its analysis.

## LOG-002

Type: Non-functional

Status: Fulfilled

The logger **shall** sample each accelerometer axis at 1 kHz.

- Rationale: Vibration analysis needs content up to 400 Hz, which requires sampling above 800 Hz.

Acceptance criteria:

- [x] A bench test measures a 1 kHz sample rate on each axis.

## LOG-003

Type: Non-functional

Status: Pending

The logger **shall** store at least 2 hours of samples in non-volatile memory.

- Rationale: The longest planned flight lasts 90 minutes; the remaining 30 minutes are margin.

Acceptance criteria:

- [ ] A 2-hour bench recording fits in the non-volatile memory.

## LOG-004

Type: Functional

Status: Underway

The logger **shall** close the current log file within 50 ms of a power-loss signal.

- Rationale: The hold-up capacitor keeps the logger powered for 80 ms after power loss.

Acceptance criteria:

- [x] The bench test closes the file within 50 ms in 100 out of 100 power cuts.
- [ ] The flight test log shows no truncated file after a power loss.

## LOG-005

Type: Functional

Status: Unfulfilled

The logger **shall** reject a configuration file whose CRC-32 does not match its content.

Acceptance criteria:

- [x] The logger rejects a configuration file with a corrupted CRC-32 in the bench test.
- [ ] The logger reports the rejection to the ground station.
