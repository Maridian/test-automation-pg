# test-automation-pg

Modular pytest test framework for embedded devices that communicate over
**CAN** or **Ethernet** — fully virtual today, hardware-ready tomorrow.

Two software elements (a "sensor" and a "controller") act as system-under-test
(SUT). They talk to each other over a pluggable link and the tests verify the
communication end-to-end. Both SUTs currently run as local subprocesses
(virtual devices); swapping in real Raspberry Pis later only requires a new
environment configuration, **not** changes to the tests.

## Structure