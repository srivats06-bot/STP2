import json
import numpy as np
from z3 import Int, Solver, And, Or, sat

PUB_FILE = "lwe_pub_params_test.json"
SEC_FILE = "lwe_secret_params_test.json"
ERR_FILE = "challenge_error_mags.json"  # file with error_magnitudes

def load_all():
    with open(PUB_FILE, "r") as f:
        pub = json.load(f)
    with open(SEC_FILE, "r") as f:
        sec = json.load(f)
    with open(ERR_FILE, "r") as f:
        err_obj = json.load(f)

    A = np.array(pub["A"], dtype=int)
    b = np.array(pub["b"], dtype=int)
    n = int(pub["lwe_n"])
    m = int(pub["lwe_m"])
    q = int(pub["lwe_q"])

    s_true = np.array(sec["s"], dtype=int)
    e_true = np.array(sec["e"], dtype=int)

    if isinstance(err_obj, dict) and "error_magnitudes" in err_obj:
        mags = err_obj["error_magnitudes"]
    else:
        mags = err_obj
    mags = [int(x) for x in mags]

    print("n, m, q =", n, m, q)
    print("A.shape =", A.shape)
    print("len(b)  =", len(b))
    print("len(mags) =", len(mags))
    print("Check |e_true| == mags:", [abs(int(x)) for x in e_true] == mags)

    # Extra consistency check
    b_re = (A @ s_true + e_true) % q
    print("Check recomputed b == b:", np.array_equal(b_re, b))
    print()

    return A, b, n, m, q, mags

def solve_lwe_with_z3_no_mod(A, b, n, m, q, error_mags):
    solver = Solver()

    s = [Int(f"s_{i}") for i in range(n)]
    e = [Int(f"e_{j}") for j in range(m)]
    k = [Int(f"k_{j}") for j in range(m)]

    # 0 <= s[i] < q
    for i in range(n):
        solver.add(And(s[i] >= 0, s[i] < q))

    # e[j] = ±mag_j
    for j in range(m):
        mag = int(error_mags[j])
        solver.add(Or(e[j] == mag, e[j] == -mag))

    # A[j]*s + e[j] = b[j] + q*k[j]
    for j in range(m):
        row_expr = sum(int(A[j, i]) * s[i] for i in range(n)) + e[j]
        solver.add(row_expr == int(b[j]) + q * k[j])

    print("[*] Solving with Z3 (no Mod)...")
    res = solver.check()
    print("Z3 result:", res)
    if res != sat:
        print("[!] UNSAT – this should not happen if files match.")
        return None, None

    model = solver.model()
    s_rec = [model.eval(s[i]).as_long() for i in range(n)]
    e_rec = [model.eval(e[j]).as_long() for j in range(m)]
    return s_rec, e_rec

def main():
    print("=== Loading data ===")
    A, b, n, m, q, mags = load_all()

    print("=== Solving LWE from A, b, q, |e| ===")
    s_rec, e_rec = solve_lwe_with_z3_no_mod(A, b, n, m, q, mags)
    if s_rec is None:
        return

    print("\nRecovered secret (first 10):", s_rec[:10])
    print("Recovered errors (first 10):", e_rec[:10])

    # Optionally compare with true secret if you want:
    with open(SEC_FILE, "r") as f:
        sec = json.load(f)
    s_true = sec["s"]
    matches = sum(1 for i in range(len(s_true)) if s_true[i] == s_rec[i])
    print(f"\nMatches with true secret: {matches}/{len(s_true)}")

    out = {
        "s_recovered": s_rec,
        "e_recovered": e_rec,
        "lwe_n": n,
        "lwe_m": m,
        "lwe_q": q,
    }
    with open("lwe_solution_z3.json", "w") as f:
        json.dump(out, f, indent=2)
    print("\n[*] Saved solution to lwe_solution_z3.json")

if __name__ == "__main__":
    main()
