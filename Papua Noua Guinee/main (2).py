import csv

G = [l.split() for l in (". . . . T T .", "# # # # ~ # #", ". . . . s s .", ". . . . s s .", ". . . . . . .", ". . H . . . .")]
A = {"NORTH": (-1, 0), "SOUTH": (1, 0), "EAST": (0, 1), "WEST": (0, -1), "FISH": (0, 0), "WAIT": (0, 0)}
B = {"s": 0.2, "T": 0.9}
water = lambda r, c: 0 <= r < 6 and 0 <= c < 7 and G[r][c] != "#"
S = [(r, c, h) for r in range(6) for c in range(7) if water(r, c) for h in range(7)]


def move(r, c, h, a, bite, tide):
    if a == "FISH":
        h += bite and h < 6 and G[r][c] in B
    elif water(r + A[a][0], c + A[a][1]):
        r, c = r + A[a][0], c + A[a][1]
    if G[r][c] == "~" and tide and water(r + 1, c):
        r += 1
    return (r, c, 0, h) if G[r][c] == "H" else (r, c, h, 0)


def solve():
    V = dict.fromkeys(S, 0.0)
    pi = {}
    for t in range(1, 25):
        N = {}
        for s in S:
            r, c, h = s
            p = B.get(G[r][c], 0)
            best = (-1, "WAIT")
            for a in A:
                q = 0
                for bite, pb in ((1, p), (0, 1 - p)):
                    for tide, pt in ((1, 0.4), (0, 0.6)):
                        r2, c2, h2, got = move(r, c, h, a, bite, tide)
                        q += pb * pt * (got + V[(r2, c2, h2)])
                if q > best[0] + 1e-12:
                    best = (q, a)
            N[s] = best[0]
            pi[(*s, t)] = best[1]
        V = N
    return pi


def main():
    pi = solve()
    with open("test-input.csv", newline="") as src, open("test-output.csv", "w", newline="") as dst:
        out = csv.writer(dst)
        out.writerow(["row", "col", "hold", "steps_left", "action"])
        for rec in csv.DictReader(src):
            s = (int(rec["row"]), int(rec["col"]), int(rec["hold"]), int(rec["steps_left"]))
            out.writerow([*s, pi.get(s, "WAIT")])


if __name__ == "__main__":
    main()
