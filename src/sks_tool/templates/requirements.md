---
type: requirements
title: Data logger requirements
description: Example requirements for a fictional flight data logger; replace them with your own.
---

<!-- What the project must satisfy; if one is not met, the project misses its
     objectives, does not work, or is unsafe. -->

## LOG-001

The logger **shall** sample each accelerometer axis at 1 kHz.

- Rationale: Vibration analysis needs content up to 400 Hz, which requires sampling above 800 Hz.

## LOG-002

The logger **shall** timestamp each sample with a resolution of 1 µs.

## LOG-003

The logger **shall** store at least 2 hours of samples in non-volatile memory.

- Rationale: The longest planned flight lasts 90 minutes; the remaining 30 minutes are margin.

## LOG-004

The logger **shall** close the current log file within 50 ms of a power-loss signal.

- Rationale: The hold-up capacitor keeps the logger powered for 80 ms after power loss.

## LOG-005

The logger **shall** reject a configuration file whose CRC-32 does not match its content.
