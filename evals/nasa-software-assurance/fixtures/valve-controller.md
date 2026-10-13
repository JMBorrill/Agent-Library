# Component description: Propellant Isolation Valve Controller (PIVC) software

- Runs on the propulsion electronics of an uncrewed lunar lander (project software class: Class B).
- Monitors tank pressure transducers at 50 Hz.
- On detection of an over-pressure condition it autonomously commands the isolation valve closed and
  sends an alarm telemetry packet to the ground.
- Hazard report HR-07 ("Propellant tank rupture") lists over-pressure as cause 2 and the PIVC software
  closure as control 2.1. A burst disk provides an independent hardware control.
