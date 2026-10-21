"""CP372 client.  Usage: python client.py [host] [port]"""
import os, socket, sys

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
DOWNLOADS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")


def recv_msg(f):
    header = f.readline().decode().strip()
    if not header:
        raise ConnectionError("Server closed the connection.")
    kind, length = header.split()
    data = f.read(int(length))
    if len(data) != int(length):
        raise ConnectionError("Connection lost mid-transfer.")
    return kind, data


def main():
    try:
        sock = socket.create_connection((HOST, PORT), timeout=10)
    except OSError as e:
        print(f"Cannot connect to {HOST}:{PORT}: {e}")
        return
    sock.settimeout(None)
    f = sock.makefile("rwb")
    try:
        kind, data = recv_msg(f)
        if kind == "ERR":
            print("Server:", data.decode())
            return
        name = data.decode()
        f.write((name + "\n").encode()); f.flush()      # communicate name to server
        print(recv_msg(f)[1].decode())

        while True:
            try:
                msg = input(f"{name}> ").strip()
            except EOFError:
                msg = "exit"
            if not msg:
                continue
            f.write((msg + "\n").encode()); f.flush()
            kind, data = recv_msg(f)
            if kind == "FILE":
                fname, content = data.split(b"\n", 1)
                os.makedirs(DOWNLOADS, exist_ok=True)
                path = os.path.join(DOWNLOADS, os.path.basename(fname.decode()))
                with open(path, "wb") as out:
                    out.write(content)
                print(f"Received '{fname.decode()}' ({len(content)} bytes) -> {path}")
            elif kind == "ERR":
                print("Error:", data.decode())
            else:
                print(data.decode())
            if msg.lower() == "exit":
                break
    except (ConnectionError, OSError) as e:
        print("Connection problem:", e)
    finally:
        f.close(); sock.close()


if __name__ == "__main__":
    main()