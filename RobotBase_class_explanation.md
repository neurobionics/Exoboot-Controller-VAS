# 🦿 Making a Robot Using the `RobotBase` Class

The `OpenSourceLeg` (OSL) library makes it simple to define your own robot by extending the `RobotBase` class. The core principle is this:

> **A robot is simply a collection of actuators and sensors.**

Your custom robot class acts as a mid-level manager that initializes, updates and safely shuts down all hardware components (sensors and actuators alike).

---

## 🧱 Core Base Classes

OSL provides three key abstract base classes:

- **`RobotBase`**: The robot's central manager. It holds and manages multiple actuators and sensors, providing lifecycle methods:
  - `start()`: Starts all components
  - `stop()`: Safely shuts down all components
  - `update()`: Called each loop iteration to run control logic
- **`ActuatorBase`**: A base class that any actuator (e.g., Dephy motors) should inherit. It defines:
  - `start()`, `stop()`, `update()` methods to control lifecycle.
- **`SensorBase`**: A base class for any sensor (IMUs, encoders, load cells), with similar lifecycle methods.

These base classes ensure modularity and reusability across different hardware setups. If you’re using the OSL’s or the Dephy Exoskeleton's default hardware, you can use the built-in actuators/sensors. Otherwise, inherit from the ActuatorBase and SensorBase classes and implement your own custom hardware!

---

## ✅ Context Manager Usage

`RobotBase` implements Python's context manager protocol with `__enter__()` and `__exit__()` methods to ensure safe resource management. When used with a 'with' block:
	1.	All actuators/sensors are automatically started
	2.	Cleanup/safe shut-down is guaranteed even if errors occur


## 📦 Exploring an Example
Using the DephyExoboots class as an example, lets understand how to devise a robot class:

The DephyExoboots class extends the RobotBase class to manage Dephy actuators and sensors, utilizing their base classes. Upon instantiation, it invokes the RobotBase __init__ method, which simply calls on the __init__ method of the DephyLegacyActuator class. 

When the DephyExoboots class is used as a context manager, it triggers the __enter__ and __exit__ methods of this RobotBase class. These methods in turn refer to the start() methods of each actuator and sensor that are part of this Exoboot robot. In this case, both DephyLegacyActuators are started -- opening ports, obtaining device IDs, and initiating data streaming.































Making a Robot using the RobotBase Class

You can devise your own robot class using the structure provided by OpenSourceLeg library's RobotBase class. The key principal to remember is that a robot is composed of a collection of actuators and/or sensors. Your robot class will essentially act as a mid-level manager, seamlessly starting and stopping all your actuators and sensors, among other actions that you desire.

The actuators and sensors that you use also have their own respective base classes that dictate basic functionality to support. Here is the breakdown of the various base classes:

    •	RobotBase: Base class for all robot systems. Provides standardized lifecycle management (start(), stop(), update()) and context manager support.
    •	ActuatorBase: Base class that actuator implementations inherit from (e.g., DephyActuator).
    •	SensorBase: Base class for any sensor (e.g., IMU, encoders, load cells).

If you’re using the OSL’s or the Dephy Exoskeleton's default hardware, you can use the built-in actuators/sensors. Otherwise, inherit from the ActuatorBase and SensorBase classes and implement your own custom class.

The RobotBase class implements __enter__() and __exit__() to ensure safe resource management. When used with a 'with' block:
	1.	All actuators/sensors are automatically started.
	2.	Cleanup is guaranteed even if errors occur.

____________________________

Using the DephyExoboots class as an example, lets understand how to devise a robot class:

The DephyExoboots class extends the RobotBase class to manage Dephy actuators and sensors, utilizing their base clas ses. Upon instantiation, it invokes the RobotBase __init__ method, which simply calls on the __init__ method of the DephyLegacyActuator class. 

When the DephyExoboots class is used as a context manager, it triggers the __enter__ and __exit__ methods of this RobotBase class. These methods in turn refer to the start() methods of each actuator and sensor that are part of this Exoboot robot. In this case, both DephyLegacyActuators are started -- opening ports, obtaining device IDs, and initiating data streaming.



    
                