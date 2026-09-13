import socket
import struct

from recordshelf.drivers.opc import opc_message
from recordshelf.drivers.wled import WledDriver, ddp_packets
from recordshelf.models import ControllerConfig


def test_ddp_packets_split_and_push_flag():
    pixels = [(i % 256, 0, 255) for i in range(500)]
    pkts = ddp_packets(pixels)
    assert len(pkts) == 2
    f0, seq0, type0, id0, off0, len0 = struct.unpack(">BBBBIH", pkts[0][:10])
    f1, _, _, _, off1, len1 = struct.unpack(">BBBBIH", pkts[1][:10])
    assert (f0, seq0, type0, id0, off0, len0) == (0x40, 0, 0x0B, 1, 0, 1440)
    assert (f1, off1, len1) == (0x41, 1440, 60)
    assert pkts[0][10:13] == bytes((0, 0, 255))
    assert pkts[1][10 + 3 * 19 :][:3] == bytes((499 % 256, 0, 255))


def test_ddp_empty_frame_is_a_push():
    pkts = ddp_packets([])
    assert len(pkts) == 1 and pkts[0][0] == 0x41 and len(pkts[0]) == 10


def test_opc_message():
    msg = opc_message([(1, 2, 3), (4, 5, 6)])
    assert msg[:4] == bytes((0, 0, 0, 6)) and msg[4:] == bytes((1, 2, 3, 4, 5, 6))


async def test_wled_http_uses_resolved_ipv4(monkeypatch):
    monkeypatch.setattr(socket, "gethostbyname", lambda host: "192.168.1.77")
    d = WledDriver(ControllerConfig(id="w", host="wled2.local", led_count=10))
    assert d.base_url == "http://wled2.local"
    await d.start()
    try:
        assert d.base_url == "http://192.168.1.77"
    finally:
        await d.stop()
