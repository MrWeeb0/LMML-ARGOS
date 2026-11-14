import json
import sys


class Strategy:
    """Variance-aware, finite-horizon upper confidence strategy."""

    def __init__(self, n_spots, n_casts):
        self.n_spots = n_spots
        self.n_casts = n_casts
        self.counts = [0] * n_spots
        self.totals = [0.0] * n_spots
        self.squares = [0.0] * n_spots

    def choose(self):
        import math

        # Several observations per spot prevent one unlucky cast from
        # permanently hiding a productive but intermittent school.
        for spot in range(self.n_spots):
            if self.counts[spot] < 5:
                return spot

        best_spot, best_score = 0, -float("inf")
        for spot in range(self.n_spots):
            n = self.counts[spot]
            mean = self.totals[spot] / n
            variance = max(1.0, self.squares[spot] / n - mean * mean)
            # MOSS-style horizon term: exploration diminishes as evidence
            # accumulates, rather than continuing at a fixed rate all day.
            exploration = max(0.0, math.log(self.n_casts / (self.n_spots * n)))
            score = (mean + 1.4 * math.sqrt(variance * exploration / n)
                     + 10.0 * exploration / n)
            if score > best_score:
                best_spot, best_score = spot, score
        return best_spot

    def update(self, spot, catch):
        self.counts[spot] += 1
        self.totals[spot] += catch
        self.squares[spot] += catch * catch


def main():
    with open("test-input.json") as f:
        rules = json.load(f)

    for _day in range(rules["n_days"]):
        agent = Strategy(rules["n_spots"], rules["n_casts"])
        for _cast in range(rules["n_casts"]):
            spot = agent.choose()
            print(spot, flush=True)
            catch = float(sys.stdin.readline())
            agent.update(spot, catch)


if __name__ == "__main__":
    main()
