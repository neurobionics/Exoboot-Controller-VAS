# Exoboot-Controller-VAS: Architecture & Design Documentation

## Overview

The Exoboot-Controller-VAS project is a modular, extensible Python-based control system for exoskeleton actuators, designed for research and development with Dephy EB51 actuators and related hardware. The system leverages multi-threading, ZeroMQ (ZMQ) for inter-thread communication, and a clear separation of concerns between hardware abstraction, control logic, state estimation, and user interface communication.

The codebase is organized to support real-time control, logging, simulation, and flexible integration with both hardware and simulated environments. It is built on top of the `opensourceleg` library, which provides base classes for actuators, robots, and sensors.

---

## Key Components

### 1. Actuator Abstraction: `DephyEB51Actuator`
- **File:** `dephyEB51.py`
- **Purpose:** Implements a hardware abstraction for the Dephy EB51 actuator, extending the `DephyLegacyActuator` from `opensourceleg`.
- **Features:**
  - Custom motor constants and safety limits.
  - Variable transmission ratio support via calibration.
  - Real-time filtering of temperature readings to prevent spikes.
  - Methods for torque/current conversion, homing/calibration, and spool control.
  - Designed for extensibility (e.g., spline assistance, JIM torque mapping).

### 2. Threading & Worker Architecture
- **File:** `threading_demo.py`
- **Purpose:** Provides a robust threading framework for running actuator control, gait state estimation, and GUI communication in parallel.
- **Key Classes:**
  - `BaseWorkerThread`: Abstract base for all worker threads, enforcing a common interface.
  - `ActuatorThread`: Handles state updates and control loop for each actuator.
  - `GaitStateEstimatorThread`: Simulates or estimates gait state for both exoskeleton sides, publishing results via ZMQ.
  - `GUICommunication`: Simulates GUI input (e.g., torque setpoints) and publishes via ZMQ.
  - `DephyExoboots`: Mini robot class managing actuators, threads, and control logic, extending `RobotBase` from `opensourceleg`.
  - `ZMQManager`: Manages ZMQ subscriber sockets for inter-thread communication.

### 3. Logging
- **File:** `non_singleton_logger.py`
- **Purpose:** Provides a flexible, non-singleton logger for per-thread or per-component logging, supporting file rotation and console output.
- **Features:**
  - Configurable log levels, formats, and file management.
  - Each logger instance is independent, avoiding global state issues.

### 4. Utilities & Constants
- **Location:** `src/utils/`, `src/settings/constants.py`, etc.
- **Purpose:** Provide reusable utilities (e.g., flexible sleeping, actuator creation, walking simulation) and centralized configuration/constants for hardware and control logic.

### 5. Simulation & Testing
- **Integration:**
  - `WalkingSimulator` (from `src.utils.walking_simulator`) is used for simulating gait cycles.
  - The main loop in `threading_demo.py` demonstrates integration of all components in a testable, modular fashion.

---

## Communication Architecture

### ZeroMQ (ZMQ) Pub/Sub
- **Pattern:** In-process (inproc) PUB/SUB sockets for fast, thread-safe communication.
- **Usage:**
  - `GaitStateEstimatorThread` publishes gait state estimates.
  - `GUICommunication` publishes user torque setpoints.
  - `ZMQManager` in the main loop subscribes to these topics and routes data to the robot logic.
- **Benefits:** Decouples threads, allows for easy scaling to multi-process or networked architectures.

---

## Control Flow & Data Flow

1. **Initialization:**
   - Actuators are created and wrapped in `DephyEB51Actuator` objects.
   - The `DephyExoboots` robot is instantiated, managing actuators and threads.

2. **Thread Startup:**
   - For each actuator, an `ActuatorThread` is started to handle real-time updates.
   - `GaitStateEstimatorThread` and `GUICommunication` threads are started for state estimation and user input, respectively.

3. **Main Loop:**
   - The main loop (using `SoftRealtimeLoop` from `opensourceleg`) subscribes to ZMQ topics for gait state and torque setpoints.
   - Data is processed and routed to the appropriate control logic (e.g., assistance generator, actuator command).

4. **Actuator Control:**
   - Each actuator thread updates its state, logs data, and (optionally) receives new setpoints from the main loop.

5. **Shutdown:**
   - The robot's `stop()` method signals all threads to quit and joins them for clean shutdown.

---

## Extensibility & Customization

- **Adding New Actuators:**
  - Extend `DephyEB51Actuator` or create new actuator classes as needed.
  - Register new actuators in the robot's actuator dictionary.

- **Custom Control Logic:**
  - Implement new worker threads or modify `iterate()` methods for advanced control schemes.
  - Use ZMQ or Python queues for inter-thread communication.

- **Simulation vs. Hardware:**
  - The architecture supports both simulated and real hardware operation, with clear abstraction boundaries.

- **Logging & Debugging:**
  - Use `NonSingletonLogger` for per-thread or per-component logging with fine-grained control.

---

## Integration with `opensourceleg`

- **Base Classes:**
  - `DephyLegacyActuator`, `RobotBase`, and `SensorBase` provide hardware abstraction and common interfaces.
- **Control Modes & Gains:**
  - Control modes (e.g., current control) and PID gains are set using methods from the base classes.
- **Logging:**
  - The system can use both the custom logger and the `opensourceleg` logger for different purposes.

---

## Example: Main Loop Data Flow

```python
# Main loop subscribes to ZMQ topics
zmq_manager = ZMQManager()
zmq_manager.setup_sub_socket("gui", "inproc://torque_setpoint")
zmq_manager.setup_sub_socket("gse", "inproc://gait_states")

for t in clock:
    gse_msg = zmq_manager.get_message("gse", key_list=["time_in_stride", "percent_gc"])
    torque = zmq_manager.get_message("gui", key_list="torque_setpoint")
    # ... process and route to actuators ...
```

---

## Design Principles

- **Separation of Concerns:** Each class/module has a clear responsibility (e.g., hardware abstraction, threading, communication, logging).
- **Thread Safety:** Uses ZMQ inproc sockets for safe, efficient inter-thread communication.
- **Extensibility:** Designed for easy addition of new actuators, sensors, control strategies, and communication interfaces.
- **Testability:** Simulation components and modular design enable unit and integration testing.
- **Robust Logging:** Per-thread logging supports debugging and traceability.

---

## Future Directions & TODOs

- Implement advanced assistance generators (e.g., spline, JIM torque mapping).
- Integrate real hardware sensors (e.g., Bertec, IMU) for gait state estimation.
- Expand GUI communication to support real-time user feedback and control.
- Refine actuator calibration and safety procedures.
- Add more comprehensive error handling and recovery mechanisms.

---

## References
- [opensourceleg Python package](https://github.com/neurobionics/opensourceleg)
- [ZeroMQ (ZMQ) Python Bindings](https://pyzmq.readthedocs.io/en/latest/)
- [Python Logging Documentation](https://docs.python.org/3/library/logging.html)

---

*This document is auto-generated and should be updated as the codebase evolves.*
