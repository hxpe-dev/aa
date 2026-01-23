import struct
import json

def send_json(sock, data):
    msg = json.dumps(data).encode("utf-8")
    length = struct.pack("!I", len(msg))
    sock.sendall(length + msg)

def recv_json(sock):
    raw_len = recvall(sock, 4)
    if not raw_len:
        return None
    msg_len = struct.unpack("!I", raw_len)[0]
    msg = recvall(sock, msg_len)
    return json.loads(msg.decode("utf-8"))

def recvall(sock, n):
    data = b""
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data
