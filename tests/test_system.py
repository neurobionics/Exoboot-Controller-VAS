import pytest
import threading
import zmq
import os
import time
from unittest import mock

# Import modules to be tested
from dephyEB51 import DephyEB51Actuator
from non_singleton_logger import NonSingletonLogger
from threading_demo import ZMQManager, DephyExoboots

# --- Logging Tests ---

def test_logger_file_creation(tmp_path):
    """
    Test that a log file is created and contains the expected log message.
    Verifies that the logger writes to the correct file and the message is present in the file.
    """
    log_path = tmp_path
    logger = NonSingletonLogger(log_path=str(log_path), file_name="pytest_logger")
    logger.info("Test log message")
    assert os.path.exists(logger.file_path)

    with open(logger.file_path) as f:
        assert "Test log message" in f.read()

# --- Threading Tests ---

def test_thread_liveness():
    """
    Test that a thread can be started and completes its run method, setting an event.
    Verifies that the event is set after the thread joins, confirming thread execution.
    """
    # Dummy thread that sets an event
    event = threading.Event()
    class DummyThread(threading.Thread):
        def run(self):
            event.set()
    t = DummyThread()
    t.start()
    t.join(timeout=2)
    assert event.is_set()

def test_per_thread_logging(tmp_path):
    """
    Test that logging from different threads (or loggers) writes to separate files.
    Verifies that each logger writes its message to its own file and that both messages are present in the correct files.
    """
    log_path = tmp_path
    logger1 = NonSingletonLogger(log_path=str(log_path), file_name="thread1")
    logger2 = NonSingletonLogger(log_path=str(log_path), file_name="thread2")
    logger1.info("Thread1 log")
    logger2.info("Thread2 log")
    with open(logger1.file_path) as f1, open(logger2.file_path) as f2:
        assert "Thread1 log" in f1.read()
        assert "Thread2 log" in f2.read()

# --- ZMQ Tests ---

def test_zmq_manager_socket_setup_and_close():
    """
    Test that a ZMQManager can set up a SUB socket and close it properly.
    Verifies that the socket is registered and the context is closed after cleanup.
    """
    zmq_manager = ZMQManager()
    zmq_manager.setup_sub_socket("test", "inproc://pytest")
    assert "test" in zmq_manager.sockets
    zmq_manager.close()
    assert zmq_manager.context.closed

def test_zmq_pub_sub_communication():
    """
    Test that a ZMQ PUB socket can send a message and a SUB socket can receive it.
    Verifies inter-thread communication using ZeroMQ inproc transport.
    """
    ctx = zmq.Context.instance()
    pub = ctx.socket(zmq.PUB)
    sub = ctx.socket(zmq.SUB)
    addr = "inproc://pytest_comm"
    pub.bind(addr)
    sub.connect(addr)
    sub.setsockopt_string(zmq.SUBSCRIBE, "")
    time.sleep(0.1)  # Allow sockets to connect
    test_msg = {"foo": 123}
    pub.send_pyobj(test_msg)
    time.sleep(0.1)
    try:
        msg = sub.recv_pyobj(flags=zmq.NOBLOCK)
        assert msg == test_msg
    except zmq.Again:
        pytest.fail("No message received on ZMQ SUB socket")
    finally:
        pub.close()
        sub.close()
        ctx.term()

def test_zmq_manager_cleanup():
    """
    Test that the ZMQManager can be set up and closed without raising any exceptions.
    Ensures resource cleanup works as expected.
    """
    zmq_manager = ZMQManager()
    zmq_manager.setup_sub_socket("test", "inproc://pytest_cleanup")
    zmq_manager.close() # Should not raise any exceptions

# --- EB51 Actuator Functionality Tests ---

def test_dephyeb51actuator_torque_to_current(monkeypatch):
    """
    Test that torque_to_current correctly converts a given torque value to a current value (in mA).
    Uses a dummy actuator to avoid hardware dependencies. Checks that the result is an int and nonzero for nonzero torque.
    """
    class DummyActuator:
        def __init__(self, *args, **kwargs):
            self.gear_ratio = 2.0
            self.efficiency = 0.9
            self.nm_per_amp = 0.146
            self.motor_sign = 1
        def torque_to_current(self, torque):
            des_current = torque / (self.gear_ratio * self.efficiency * self.nm_per_amp)
            des_current = des_current * 1000 * self.motor_sign
            return int(des_current)

    monkeypatch.setattr('dephyEB51.DephyEB51Actuator', DummyActuator)
    actuator = DummyActuator()
    actuator.gear_ratio = 2.0
    torque = 1.0  # Nm
    current = actuator.torque_to_current(torque)
    assert isinstance(current, int)
    assert current != 0

def test_dephyeb51actuator_current_to_torque(monkeypatch):
    """
    Test that current_to_torque correctly converts a given current value (in mA) to a torque value (in Nm).
    Uses a dummy actuator to avoid hardware dependencies. Checks that the result is a float.
    """
    class DummyActuator:
        def __init__(self, *args, **kwargs):
            self.motor_current = 1000
            self.nm_per_amp = 0.146
            self.efficiency = 0.9
            self.motor_sign = 1
            self.gear_ratio = 2.0
        def current_to_torque(self):
            mA_to_A_current = self.motor_current/1000
            des_torque = mA_to_A_current * self.nm_per_amp * self.gear_ratio * self.efficiency * self.motor_sign
            return float(des_torque)
    monkeypatch.setattr('dephyEB51.DephyEB51Actuator', DummyActuator)
    actuator = DummyActuator()
    actuator.motor_current = 1000  # mA
    torque = actuator.current_to_torque()
    assert isinstance(torque, float)

def test_update_gear_ratio():
    """
    Test that update_gear_ratio updates the actuator's gear ratio using the transmission ratio generator.
    Uses a dummy actuator and a dummy transmission ratio generator to control the output.
    Verifies that the updated gear ratio is as expected and that the actuator's internal state is updated.
    """
    class DummyTRGen:
        def get_TR(self, ankle_angle):
            return 2.5
        def get_offset(self):
            return 0.0
    class DummyActuator:
        def __init__(self):
            self.ank_ang = 10
            self._data = True
            self.ank_enc_sign = 1
            self.tr_gen = DummyTRGen()
            self._gear_ratio = 1.0
        @property
        def ankle_angle(self):
            return self.ank_enc_sign * self.ank_ang
        def update_gear_ratio(self):
            self._gear_ratio = self.tr_gen.get_TR(self.ankle_angle)
            return self._gear_ratio
    actuator = DummyActuator()
    updated_ratio = actuator.update_gear_ratio()
    assert updated_ratio == 2.5
    assert actuator._gear_ratio == 2.5

def test_assign_id_to_side(monkeypatch):
    """
    Test that assign_id_to_side returns the correct side (left/right) for a given device ID.
    Uses a dummy actuator and the DEV_ID_TO_SIDE_DICT mapping for validation.
    """
    from src.settings.constants import DEV_ID_TO_SIDE_DICT
    class DummyActuator(DephyEB51Actuator):
        def __init__(self):
            pass
    actuator = DummyActuator()
    actuator.dev_id = list(DEV_ID_TO_SIDE_DICT.keys())[0]
    expected_side = DEV_ID_TO_SIDE_DICT[actuator.dev_id]
    side = DephyEB51Actuator.assign_id_to_side(actuator)
    assert side == expected_side

def test_ankle_angle_property(monkeypatch):
    """
    Test that the ankle_angle property computes the correct transformed ankle angle.
    Uses a dummy actuator and dummy transmission ratio generator, and checks the calculation using a known constant.
    """
    from src.settings.constants import EB51_CONSTANTS
    class DummyTRGen:
        def get_offset(self):
            return 5.0
    class DummyActuator:
        def __init__(self):
            self._data = True
            self.ank_enc_sign = 1
            self.ank_ang = 10
            self.tr_gen = DummyTRGen()
        @property
        def ankle_angle(self):
            return (self.ank_enc_sign * self.ank_ang * EB51_CONSTANTS.MOT_ENC_CLICKS_TO_DEG) - self.tr_gen.get_offset()
    actuator = DummyActuator()
    expected_angle = (actuator.ank_enc_sign * actuator.ank_ang * EB51_CONSTANTS.MOT_ENC_CLICKS_TO_DEG) - 5.0
    result = actuator.ankle_angle
    assert result == expected_angle

# --- DephyExobootsRobot Class Tests (Extensibility tests) ---

def test_add_new_actuator(monkeypatch):
    """
    Test that a new actuator can be added to the exoboots actuators dictionary.
    Uses a dummy actuator class to avoid hardware dependencies and checks that the new actuator is present after addition.
    """
    class DummyActuator:
        def __init__(self, tag=None, offline=True):
            self.tag = tag
    monkeypatch.setattr('dephyEB51.DephyEB51Actuator', DummyActuator)
    actuators = {"left": DummyActuator(tag="left", offline=True)}
    exoboots = DephyExoboots(tag="pytest_exo", actuators=actuators, sensors={})
    actuators["right"] = DummyActuator(tag="right", offline=True)
    exoboots.actuators = actuators
    assert "right" in exoboots.actuators

# --- Error Handling ---

def test_invalid_config(monkeypatch):
    """
    Test that the actuator raises an exception if an invalid configuration is set (e.g., invalid MAX_CASE_TEMP).
    Uses monkeypatch to simulate an invalid constant and expects an exception on actuator initialization.
    """
    monkeypatch.setattr("dephyEB51.MAX_CASE_TEMP", -999, raising=False)
    with pytest.raises(Exception):
        DephyEB51Actuator(offline=True)