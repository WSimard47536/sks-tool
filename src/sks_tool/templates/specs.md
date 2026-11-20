---
type: specs
title: Data logger specs
description: Example design decisions for a fictional flight data logger; replace them with your own.
---

<!-- How it is built: diagrams, the design choices made, and why. -->

## LOG-S-001

Type: Non-functional

Status: Fulfilled

The logger writes samples to a ring buffer in RAM and flushes it to flash every second.

- Rationale: Flash writes are slow and wear the memory; batching keeps up with 1 kHz sampling.

Acceptance criteria:

- [x] The buffer never overflows at 1 kHz on all axes in the bench test.

![Ring buffer design](LOG-S-001.drawio.svg)

## LOG-S-002

Type: Functional

Status: Underway

The logger names each log file after its power-on count, so files never overwrite each other.

- Rationale: The logger has no real-time clock, so a counter is the only name unique across sessions.

Acceptance criteria:

- [x] Two consecutive sessions in the bench test produce two separate files.
- [ ] The power-on count survives a firmware update.

## LOG-S-003

Type: Non-functional

Status: Pending

The configuration file is a fixed-layout binary record checked with a CRC-32.

- Rationale: A fixed layout is simple to parse on the logger and to check from the ground tools.

Acceptance criteria:

- [ ] The ground tool and the logger read the same test file identically.
