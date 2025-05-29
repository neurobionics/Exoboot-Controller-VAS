import pytest
from src.utils.actuator_utils import get_active_ports, create_actuators
from unittest import mock

# Test get_active_ports (mocking sys.platform and glob/serial)
def test_get_active_ports_linux(monkeypatch):
    """
    Test that get_active_ports returns the expected port on a Linux system
    when a dummy serial port is present and can be opened.
    """
    monkeypatch.setattr('sys.platform', 'linux')
    monkeypatch.setattr('glob.glob', lambda pattern: ['/dev/ttyACM0'])
    class DummySerial:
        def __init__(self, port): pass
        def close(self): pass
    monkeypatch.setattr('serial.Serial', DummySerial)
    ports = get_active_ports()
    assert '/dev/ttyACM0' in ports

def test_get_active_ports_no_ports(monkeypatch):
    """
    Test that get_active_ports returns an empty list when no ports are found.
    """
    monkeypatch.setattr('sys.platform', 'linux')
    monkeypatch.setattr('glob.glob', lambda pattern: [])
    ports = get_active_ports()
    assert ports == []

# Test create_actuators (mocking get_active_ports and DephyEB51Actuator)
def test_create_actuators(monkeypatch):
    """
    Test that create_actuators creates an actuator dictionary with the correct
    side key and actuator instance, using mocked get_active_ports and actuator class.
    """
    monkeypatch.setattr('src.utils.actuator_utils.get_active_ports', lambda: ['/dev/ttyACM0'])
        
    class DummyActuator:
        def __init__(self, port, baud_rate, frequency, debug_level):
            self.side = 'left'
            self.tag = 'left'
            self.dev_id = 888
            self.motor_sign = 1
            self.ank_enc_sign = 1
    monkeypatch.setattr('src.utils.actuator_utils.DephyEB51Actuator', DummyActuator)
    actuators = create_actuators(1, 230400, 1000, 3)
    assert 'left' in actuators
    assert isinstance(actuators['left'], DummyActuator)

def test_create_actuators_no_ports(monkeypatch):
    """
    Test that create_actuators raises NoActuatorsFoundError when no ports are found.
    """
    from src.utils.actuator_utils import NoActuatorsFoundError
    monkeypatch.setattr('src.utils.actuator_utils.get_active_ports', lambda: [])
    with pytest.raises(NoActuatorsFoundError):
        create_actuators(1, 230400, 1000, 3)
