import json
import socket
import base64
import sys

HOST = "filtermaze.2025.ctfcompetition.com"
PORT = 1337

# ======================
# Graph loading
# ======================
with open("graph.json", "r") as f:
    graph = {int(k): v for k, v in json.load(f).items()}

# ======================
# Generic socket helpers
# ======================
def recv_line(sock):
    data = b""
    while not data.endswith(b"\n"):
        chunk = sock.recv(1)
        if not chunk:
            break
        data += chunk
    return data.decode("utf-8", errors="replace")

def send_cmd(sock, obj):
    msg = json.dumps(obj) + "\n"
    sock.sendall(msg.encode())
    while True:
        resp_line = recv_line(sock)
        if resp_line == "":
            raise RuntimeError("Connection closed by remote")

        resp_line = resp_line.strip()
        if not resp_line:
            continue

        print("SERVER LINE:", repr(resp_line))

        try:
            return json.loads(resp_line)
        except json.JSONDecodeError:
            # Not JSON (banner / debug text), keep reading
            continue

# ======================
# PoW logic (from official kctf-pow)
# ======================
VERSION = "s"
MODULUS = 2**1279 - 1

def decode_number(enc: str) -> int:
    return int.from_bytes(base64.b64decode(enc.encode()), "big")

def encode_number(num: int) -> str:
    size = (num.bit_length() // 24) * 3 + 3
    return base64.b64encode(num.to_bytes(size, "big")).decode()

def decode_challenge(enc: str):
    parts = enc.split(".")
    if parts[0] != VERSION:
        raise Exception("Unknown challenge version")
    return [decode_number(p) for p in parts[1:]]

def encode_challenge(arr):
    return ".".join([VERSION] + [encode_number(x) for x in arr])

def python_sloth_root(x: int, diff: int, p: int) -> int:
    exponent = (p + 1) // 4
    for i in range(diff):
        # simple progress indicator every few iterations
        if diff >= 20 and i % (diff // 10) == 0:
            print(f"[PoW] progress: {i}/{diff}")
        x = pow(x, exponent, p) ^ 1
    print(f"[PoW] progress: {diff}/{diff}")
    return x

def solve_challenge(chal: str) -> str:
    parts = decode_challenge(chal)
    # Expect [diff, x]; if more appear, treat first as diff, second as x
    diff = parts[0]
    x = parts[1]
    print(f"[PoW] difficulty = {diff}")
    y = python_sloth_root(x, diff, MODULUS)
    return encode_challenge([y])
# ===== PoW helpers (you should already have these above, keep them) =====
import base64

VERSION = "s"
MODULUS = 2**1279 - 1  # big prime

def decode_number(enc: str) -> int:
    return int.from_bytes(base64.b64decode(enc.encode()), "big")

def encode_number(num: int) -> str:
    size = (num.bit_length() // 24) * 3 + 3
    return base64.b64encode(num.to_bytes(size, "big")).decode()

def decode_challenge(enc: str):
    parts = enc.split(".")
    if parts[0] != VERSION:
        raise Exception("Unknown challenge version")
    return [decode_number(p) for p in parts[1:]]

def encode_challenge(arr):
    return ".".join([VERSION] + [encode_number(x) for x in arr])

def python_sloth_root(x: int, diff: int, p: int) -> int:
    exponent = (p + 1) // 4
    for i in range(diff):
        # simple progress prints so it doesn't look frozen
        if diff >= 20 and i % max(1, diff // 10) == 0:
            print(f"[PoW] progress: {i}/{diff}")
        x = pow(x, exponent, p) ^ 1
    print(f"[PoW] progress: {diff}/{diff}")
    return x

def solve_challenge(chal: str) -> str:
    parts = decode_challenge(chal)
    # Take the first two numbers as (difficulty, x)
    diff = parts[0]
    x = parts[1]
    print(f"[PoW] difficulty = {diff}")
    y = python_sloth_root(x, diff, MODULUS)
    return encode_challenge([y])

# ===== REPLACE YOUR OLD solve_pow WITH THIS =====
def solve_pow(sock):
    """
    Automatically:
    - read until the 'python3 ... solve <challenge>' line
    - extract <challenge>
    - solve PoW
    - send solution immediately (no waiting for 'Solution?' line)
    - read one result line
    """
    challenge_str = None

    while True:
        line = recv_line(sock)
        if line == "":
            raise RuntimeError("Server closed before PoW challenge")
        line_stripped = line.strip()
        print("POW LINE:", repr(line_stripped))

        # The line containing "solve <challenge>"
        if "solve " in line_stripped and "kctf-pow" in line_stripped:
            challenge_str = line_stripped.split()[-1]
            print("\n[PoW] Challenge from server:\n", challenge_str, "\n")
            break  # <-- IMPORTANT: stop waiting further, go solve now

    if not challenge_str:
        raise RuntimeError("Did not find PoW challenge string")

    # Now solve
    print("[PoW] Solving, this can take a while...")
    solution = solve_challenge(challenge_str)
    print("[PoW] Solution =", solution)

    # Send solution (server is ready even if it didn't print 'Solution?')
    sock.sendall((solution + "\n").encode())

    # Read one line of result ('Correct' or 'fail' etc.)
    result_line = recv_line(sock).strip()
    print("[PoW] Result line:", repr(result_line))
    if "fail" in result_line.lower():
        raise RuntimeError("PoW failed: " + result_line)

    print("[PoW] Completed successfully.\n")


# ======================
# Maze logic
# ======================
def main():
    s = socket.socket()
    s.connect((HOST, PORT))

    # 1) Solve PoW
    solve_pow(s)

    # 2) Maze oracle
    path = []
    error_mags = None

    while error_mags is None:
        if not path:
            candidates = list(range(30))  # first node
        else:
            candidates = graph[path[-1]]  # neighbors

        found_extension = False
        for v in candidates:
            segment = path + [v]
            print("Trying segment:", segment)
            resp = send_cmd(s, {"command": "check_path", "segment": segment})
            print("Response:", resp)

            status = resp.get("status")
            if status == "valid_prefix":
                path.append(v)
                found_extension = True
                break
            elif status == "path_complete":
                path.append(v)
                error_mags = resp["lwe_error_magnitudes"]
                found_extension = True
                break
            # "path_incorrect" → try next v

        if not found_extension:
            raise RuntimeError("No valid extension found; something is wrong.")

    print("\nRecovered path:", path)
    print("Length:", len(path))
    print("\nRecovered |e| (error magnitudes) =", error_mags)

    with open("error_magnitudes.json", "w") as f:
        json.dump(error_mags, f)

    s.close()

if __name__ == "__main__":
    main()
