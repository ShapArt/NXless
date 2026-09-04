from __future__ import annotations

import socket
import threading

class EchoServer:
    def __init__(self, host: str, tcp_port: int = 5001, udp_port: int = 5002) -> None:
        self.host = host
        self.tcp_port = tcp_port
        self.udp_port = udp_port
        self._stop = threading.Event()
        self._tcp: socket.socket | None = None
        self._udp: socket.socket | None = None
        self._threads: list[threading.Thread] = []

    def start(self) -> None:
        tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tcp.bind((self.host, self.tcp_port))
        tcp.listen()
        tcp.settimeout(0.2)
        self.tcp_port = int(tcp.getsockname()[1])
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp.bind((self.host, self.udp_port))
        udp.settimeout(0.2)
        self.udp_port = int(udp.getsockname()[1])
        self._tcp, self._udp = tcp, udp
        self._threads = [
            threading.Thread(target=self._tcp_loop, name="nxless-tcp-echo", daemon=True),
            threading.Thread(target=self._udp_loop, name="nxless-udp-echo", daemon=True),
        ]
        for thread in self._threads:
            thread.start()

    def stop(self) -> None:
        self._stop.set()
        for sock in (self._tcp, self._udp):
            if sock is not None:
                try:
                    sock.close()
                except OSError:
                    pass
        for thread in self._threads:
            thread.join(timeout=1.0)

    def _tcp_loop(self) -> None:
        assert self._tcp is not None
        while not self._stop.is_set():
            try:
                conn, _ = self._tcp.accept()
            except (socket.timeout, OSError):
                continue
            threading.Thread(target=self._handle_tcp, args=(conn,), daemon=True).start()

    @staticmethod
    def _handle_tcp(conn: socket.socket) -> None:
        with conn:
            while True:
                data = conn.recv(65536)
                if not data:
                    return
                conn.sendall(data)

    def _udp_loop(self) -> None:
        assert self._udp is not None
        while not self._stop.is_set():
            try:
                data, addr = self._udp.recvfrom(65536)
            except (socket.timeout, OSError):
                continue
            try:
                self._udp.sendto(data, addr)
            except OSError:
                if not self._stop.is_set():
                    raise
