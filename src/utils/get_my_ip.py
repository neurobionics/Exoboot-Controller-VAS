import socket


def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't need to be reachable, just used to get the local IP
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        # if connection fails, fallback to localhost
        ip = "10.0.0.200"
    finally:
        s.close()

    return ip
