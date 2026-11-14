"""Exact A* search over position, bridge configuration and tidal phase."""
import heapq
import sys
import environment


def solve(valley):
    cells = [(r, c) for r, row in enumerate(valley.grid)
             for c, ch in enumerate(row) if ch not in '#=']
    index = {p: i for i, p in enumerate(cells)}
    count = len(cells)
    bridges = {ch: 1 << i for i, ch in enumerate(sorted(valley.bridges))}
    required = [bridges.get(valley.cell(*p), 0) for p in cells]
    toggles = [sum(bridges[b] for b in valley.winches.get(valley.cell(*p), ()))
               for p in cells]
    fords = [valley.cell(*p) == '~' for p in cells]
    edges = [[] for _ in cells]
    reverse = [[] for _ in cells]
    for i, (r, c) in enumerate(cells):
        for action, dr, dc in [('U', -1, 0), ('D', 1, 0), ('L', 0, -1), ('R', 0, 1)]:
            j = index.get((r + dr, c + dc))
            if j is not None:
                cost = valley.duration(r, c, r + dr, c + dc)
                edges[i].append((j, cost, action))
                reverse[j].append((i, cost))
        edges[i].append((i, 1, 'W'))
    start, goal = index[valley.start], index[valley.goal]
    # Admissible lower bound: remove tide and bridge restrictions, while
    # retaining exact directed terrain costs.
    h = [10**12] * count
    h[goal] = 0
    queue = [(0, goal)]
    while queue:
        d, i = heapq.heappop(queue)
        if d != h[i]:
            continue
        for j, cost in reverse[i]:
            nd = d + cost
            if nd < h[j]:
                h[j] = nd
                heapq.heappush(queue, (nd, j))
    period = valley.tide_period
    mask = sum(bridges[b] for b in valley.initial_open)
    initial = mask * count * period + start * period
    distances = {initial: 0}
    parents = {}
    queue = [(h[start], 0, initial)]
    while queue:
        _, time, state = heapq.heappop(queue)
        if distances.get(state) != time:
            continue
        packed, phase = divmod(state, period)
        mask, i = divmod(packed, count)
        if i == goal:
            route = []
            while state != initial:
                state, action = parents[state]
                route.append(action)
            return ''.join(reversed(route)), time
        for j, cost, action in edges[i]:
            nt = time + cost
            phase = nt % period
            if required[j] and not (mask & required[j]):
                continue
            if fords[j] and phase >= valley.tide_low:
                continue
            nm = mask ^ toggles[j] if j != i else mask
            ns = (nm * count + j) * period + phase
            if nt < distances.get(ns, 10**12):
                distances[ns] = nt
                parents[ns] = (state, action)
                heapq.heappush(queue, (nt + h[j], nt, ns))
    raise RuntimeError('No route reaches G')


def main():
    valley = environment.load_map('test-input.txt')
    route, minutes = solve(valley)
    trace = environment.simulate(valley, route)
    assert trace[-1][0] == minutes
    with open('solution.txt', 'w', encoding='ascii') as handle:
        handle.write(route + '\n')
    print('Valid route: {} minutes'.format(minutes), file=sys.stderr)


if __name__ == '__main__':
    main()
