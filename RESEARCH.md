# ASIB Research Positioning

Last reviewed: 2026-10-04

## Why ASIB exists

Current space autonomy work already covers important pieces such as event-driven onboard operations, high-performance spacecraft computing, autonomous navigation, robotic servicing, and in-space manipulation.

ASIB therefore does **not** claim to invent:
- autonomous spacecraft operations by itself
- orbital data centers by themselves
- satellite-servicing robots by themselves
- onboard AI inference by itself

## Proposed ASIB research layer

ASIB investigates a different systems problem:

> How can a distributed set of heterogeneous off-Earth infrastructure nodes coordinate compute, power, thermal headroom, communications, maintenance and recovery under partial observability and intermittent Earth contact?

The key architectural idea is a **cross-infrastructure autonomy layer** rather than a single spacecraft controller.

### V2 prototype results

The current Earth testbed now models observer-specific state, delayed synchronization, network partitions, uncertainty penalties, execution-time target revalidation, explicit safety invariants, maintenance-robot simulation and reproducible recovery metrics. This is a research prototype rather than evidence that the architecture is flight-qualified.

### Research questions

1. Can infrastructure workloads be reallocated while preserving critical service?
2. Can power and thermal constraints be treated as first-class scheduling signals?
3. Can a network of autonomous nodes remain useful during communication delay or partition?
4. Can recovery decisions be verified against explicit safety policies before they are executed?
5. Can operational experience be represented in a form transferable across different node types?
6. How should humans intervene when the autonomous planner cannot find a safe plan?

## Relevant public work to study

- NASA, "New Onboard Capability to Enable Autonomous Spacecraft Operations" (Apr. 28, 2026):
  https://science.nasa.gov/science-research/science-enabling-technology/technology-highlights/new-onboard-capability-to-enable-autonomous-spacecraft-operations/
- NASA, "High Performance Spaceflight Computing" (May 8, 2026):
  https://www.nasa.gov/directorates/stmd/nasa-industry-advance-high-performance-spaceflight-computing/
- DARPA, "Robotic Servicing of Geosynchronous Satellites technology to launch in 2026" (May 20, 2026):
  https://www.darpa.mil/news/2026/robotic-servicing-geosynchronous-satellites-technology-launch-2026
- NASA, "Robotic Servicing Mission Launches with NASA Support" (Jul. 22, 2026):
  https://www.nasa.gov/technology/robotic-servicing-mission-launches-with-nasa-support/
- NASA, "Robotically Manipulated Payload Challenge" (2026):
  https://www.nasa.gov/stmd-flight-opportunities/access-flight-tests/nasa-techleap-prize-information/robotically-manipulated-payload-challenge/

## Intellectual property note

This repository is an experimental implementation, not a patent opinion. Before filing or publishing a patent-sensitive disclosure, perform a dedicated prior-art and patent search and document the novel claims independently.
