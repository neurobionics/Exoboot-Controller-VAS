# Exoboot-Controller-VAS: Test Plan for Reliability, Concurrency, and Functionality

## Purpose
This test plan is designed to systematically surface and address potential issues in the Exoboot-Controller-VAS system, with a focus on reliability, concurrency, and functionality. The plan covers both automated and manual tests, and is intended to be updated as the codebase evolves.

---

## 1. Reliability Tests

### 1.1 Error Handling
- **Test:** Simulate hardware disconnects (e.g., unplug actuator, kill sensor process) and verify the system logs the error, attempts recovery, and does not crash.
- **Test:** Force ZMQ publisher/subscriber failures and check for graceful error handling and logging.
- **Test:** Inject invalid configuration values and verify the system detects and reports misconfiguration at startup.
- **Test:** Simulate file system errors (e.g., log directory unwritable) and verify logger fallback or error reporting.

### 1.2 Actuator Safety
- **Test:** Exceed actuator safety limits (e.g., overcurrent, overtemperature) and verify the actuator is safely disabled and a warning is logged.
- **Test:** Simulate sensor failure (e.g., encoder stuck or out-of-range) and verify the system enters a safe state.

### 1.3 Logging and Alerting
- **Test:** Trigger critical errors and verify they are logged at the correct level and, if possible, escalate to user/operator.

---

## 2. Concurrency Tests

### 2.1 Thread Liveness and Coordination
- **Test:** Kill or hang a worker thread (e.g., ActuatorThread, GaitStateEstimatorThread) and verify the main process detects the failure (e.g., via watchdog or health check).
- **Test:** Rapidly start and stop threads to check for resource leaks or deadlocks.
- **Test:** Simulate a slow or blocked ZMQ publisher and verify subscribers do not hang indefinitely.

### 2.2 Shared State and Race Conditions
- **Test:** If any shared state exists, run stress tests with multiple threads accessing/updating the state to check for race conditions or data corruption.

### 2.3 Shutdown and Cleanup
- **Test:** Issue a shutdown command during normal operation and verify all threads terminate cleanly and resources (sockets, files) are released.
- **Test:** Simulate a forced shutdown (e.g., SIGINT) and verify the system does not leave hardware in an unsafe state.

---

## 3. Functionality Tests

### 3.1 Feature Completeness
- **Test:** Validate the variable transmission ratio and torque/current conversion logic with known inputs/outputs.

### 3.2 Communication and Data Flow
- **Test:** Verify ZMQ pub/sub communication for all topics (gait state, torque setpoint) under normal and high-load conditions.
- **Test:** Simulate message loss or out-of-order delivery and verify system robustness.
- **Test:** Test GUI input handling, including invalid or rapid user input.

### 3.3 Logging and Debugging
- **Test:** Enable debug logging in all threads and verify logs are complete, non-duplicated, and do not impact real-time performance.
- **Test:** Check that log files are created per-thread as expected and can be correlated for debugging.

### 3.4 Extensibility
- **Test:** Add a new actuator or sensor and verify it can be integrated without breaking existing functionality.
- **Test:** Add a new worker thread and verify it can communicate via ZMQ and be managed by the main process.

---

## 4. Manual and Automated Test Procedures
- **Automated Tests:**
  - Develop unit tests for all utility functions, actuator logic, and communication handlers.
  - Develop integration tests for thread startup/shutdown, ZMQ communication, and actuator-sensor loops.
- **Manual Tests:**
  - Perform hardware-in-the-loop tests for actuator safety and calibration.
  - Simulate user input and error scenarios not easily automated.

---

## 5. Test Coverage and Reporting
- **Test each major code path, including error and edge cases.**
- **Log all test results and failures for traceability.**
- **Update this test plan as new features or issues are identified.**

---

## 6. Open Issues and Recommendations
- Implement watchdogs or health checks for all worker threads.
- Add more robust error handling and recovery for hardware and communication failures.
- Expand automated test coverage, especially for concurrency and error scenarios.
- Consider adding a test harness for hardware-in-the-loop and simulation-based regression testing.

---

*This test plan is a living document and should be updated as the system evolves.*
