Bihainim Angkol (Follow Your Uncle): Solution and Documentation
Summary
The submitted agent does not copy angkol. It computes the best possible action for every situation the canoe can be in, using the exact rules of the lagoon, and it goes to the outer reef where fish bite 90 percent of the time, while angkol stays on the seagrass where they bite 20 percent of the time. On the 400 practice days it lands 5.963 fish per day against angkol's 2.490, which is 2.395 times angkol. The required ratio is 1.5. The whole solution is one self-contained file, main.py, that runs in about 0.09 seconds.
The task in plain words
A village on Kimbe Bay, in West New Britain, fishes from an outrigger canoe. Angkol, the uncle, has fished the same careful way for thirty years. His nephew or niece kept a logbook of 400 days. The family wants an agent that first learns to fish like him and then does better, landing at least 1.5 times as many fish per day on days it has not seen.
What has to be submitted:
A single file called main.py.
When run, it reads test-input.csv from its working directory and writes test-output.csv with the header row,col,hold,steps_left,action and exactly one row per input row.
Each action must be one of NORTH, SOUTH, EAST, WEST, FISH, WAIT.
It runs alone, next to test-input.csv only, so the policy has to be inside the file. Allowed: Python 3.12, the standard library and numpy 2.2.6, no internet, 60 seconds.
Scoring is all or nothing. An average catch of at least 1.5 times angkol's, on the same days and under the same tide and bites, passes (200 points) and releases the flag. Anything lower, a crash, a timeout, or an output with a missing, repeated or unknown state fails. Angkol's average is 2.49 fish per day, so the target is 3.735.
The lagoon and its rules
    0 1 2 3 4 5 6
 0  . . . . T T .        H  village beach: fish are landed here
 1  # # # # ~ # #        s  seagrass flats      T  outer reef drop-off
 2  . . . . s s .        #  barrier reef (no canoe crosses it)
 3  . . . . s s .        ~  reef passage        .  open water
 4  . . . . . . .
 5  . . H . . . .
Rule
Detail
Day length
24 steps. The day starts on the beach at row 5, column 2 with an empty hold.
State
(row, col, hold, steps_left). The hold has 0 to 6 fish. steps_left counts down from 24 to 1. There are 36 cells a canoe can be on, so there are 36 x 7 x 24 = 6,048 states.
Moving
NORTH, SOUTH, EAST and WEST move one cell. Moving into the barrier reef or off the map leaves the canoe where it is.
Fishing
FISH on a fishing ground with fewer than 6 fish aboard adds one fish with a chance that depends on the ground: 20 percent on seagrass (s) and 90 percent on the outer reef (T). Anywhere else it catches nothing.
Waiting
WAIT does nothing.
Tide
If a step ends with the canoe on the passage (row 1, column 4), there is a 40 percent chance the tide pushes it one cell south, back into the lagoon.
Landing
Whenever the canoe is on the beach, everything in the hold is landed. The day's score is the number of fish landed. Fish still aboard when the day ends are lost.
Randomness
Every chance event comes from the day's seed, so the same seed and the same decisions always give the same day. The agent only sees the state, not the random numbers.

The barrier reef has a single gap, the passage at row 1, column 4. The only way to the outer reef, where the fish bite best, is through that gap.
The files in the task
File
What it is
Submitted?
lagoon.py
The simulator. It holds every rule and constant above (class Lagoon with reset and step), plus helpers to play days (play_day), read and write policy files, check a policy file, export a main.py, and compare a policy with angkol.
No
dataset/logbook.csv
Angkol's 400 days, one row per decision: day, row, col, hold, steps_left, action, reward.
No
train-input.csv
Practice input: every one of the 6,048 states.
No
train-output.json
The 400 practice days and angkol's catch on each, his mean of 2.49 and the target ratio of 1.5.
No
main.py
The submission. The template only waited on the beach and landed nothing. Ours holds the real agent.
Yes

What angkol's logbook shows
The logbook has 400 days of 24 decisions each, so 9,600 rows. The rewards add up to exactly his mean of 2.49 fish per day.
He never goes north of the barrier reef. There is not a single logbook row in row 0 or row 1, so he never uses the passage and never visits the outer reef.
99.1 percent of his FISH actions are on seagrass, and 4,424 of his 5,000 FISH actions are on one cell, row 3, column 4.
46 of his 400 days landed nothing, and his best day was 6 fish.
On day 1 he walked north to row 3, went east to column 4, fished 15 times, and landed 2 fish three steps before the end.
Seagrass gives 0.2 fish per fishing step. Even a day spent only fishing there would be limited by that rate, and angkol also spends steps walking and waiting. This is why copying him cannot reach 1.5 times his catch. The outer reef gives 0.9 fish per fishing step, four and a half times more, at the price of a longer trip.
The idea behind the solution
A policy is a table that says which action to take in every state. The agent cannot see the random numbers, only the state, and the random numbers are different on every day. So the best policy is the one that maximizes the average number of fish landed. The probabilities are known exactly (0.2, 0.9 and 0.4), so we do not need to learn them from data or approximate them. We can compute the best action for every state directly.
The method is backward induction, a form of dynamic programming:
Define V(t, state) as the average number of fish that will still be landed from this state with t steps left, if the canoe plays as well as possible from here on.
With 0 steps left nothing more can be landed, so V(0, state) = 0. Fish still aboard are lost.
For t = 1, 2, ..., 24, and for every state, try each of the six actions. A step has four possible chance outcomes: bite or no bite, and tide push or no tide push. For each outcome work out the next state and the fish landed in this step. The value of an action is the sum over the four outcomes of probability x (fish landed now + V(t - 1, next state)).
Keep the action with the highest value as the policy for (state, t), and keep its value as V(t, state).
Example: with 1 step left at row 5, column 3 holding 6 fish, WEST moves to the beach and lands 6, so the value is 6 and the policy chooses WEST. With 2 steps left at row 5, column 4 holding 6 fish, two WEST moves land 6 again. Working backwards in this way, the values spread out to every other state, including the trip to the reef.
The work is small: 252 combinations of position and hold x 24 time steps x 6 actions x 4 chance outcomes is about 145,000 evaluations.
The result is a plan that fits the numbers. A round trip to the outer reef needs at least 14 steps (7 each way), the hold fills in about 7 fishing steps at a 90 percent bite chance, and the tide at the passage can delay the canoe. That leaves enough slack in 24 steps for one full trip, and a second trip would need at least another 14 steps, which does not fit.
main.py, part by part
The map and constants
G is the map as a grid of cells. A lists the six actions with their row and column movement (FISH and WAIT do not move). B gives the bite chance per fishing ground: 0.2 on seagrass and 0.9 on the outer reef. These are copied from lagoon.py.
water and S
water(r, c) is true for every cell a canoe can be on, which is any cell on the map that is not barrier reef. S lists every combination of position and hold, 36 cells x 7 holds = 252.
move
move(r, c, h, a, bite, tide) applies one action with its chance events already decided and returns the new row, column, hold and the fish landed. It follows the simulator exactly: FISH adds a fish only on a fishing ground, with room in the hold and a bite; a move happens only into water; the tide pushes the canoe south only if it ends on the passage and the cell below is water; and landing on the beach empties the hold and counts the fish.
solve
solve() is the backward induction. It starts with V = 0 for every state, then repeats for t from 1 to 24: for each state and each action it adds up probability x (fish landed + value of the next state) over the four chance outcomes, and stores the best action in pi under the key (row, col, hold, steps_left). A new action replaces the current best only if it is better by more than 1e-12, so equal choices keep the first one in the list. It returns the policy table.
main
main() builds the table, reads test-input.csv, and for each row writes the state followed by its best action to test-output.csv. A state that is somehow not in the table gets WAIT, which is always a valid action. The output has the required header and one row per input row, in the same order.
The full file
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
A day played by the agent
This is day 7 of the practice days, replayed with the agent's policy. It shows the plan in action, including two tide setbacks.
Steps left
Position (row, col)
Hold
Action
What happens
24 to 22
(5,2) to (3,2)
0
NORTH x3
Leaves the beach and heads north.
21 and 20
(2,2), (2,3)
0
EAST x2
Moves along row 2 to the foot of the passage.
19, 18, 17
(2,4)
0
NORTH x3
The canoe enters the passage twice and the tide pushes it back to (2,4) each time. The third attempt gets through.
16
(1,4)
0
NORTH
In the passage, not pushed this time.
15 to 10
(0,4)
0 to 5
FISH x6
On the outer reef every cast brings a fish. The hold is full (6) after the sixth.
9 and 8
(0,4)
6
NORTH x2
The canoe is already at the top edge, so this leaves it in place. It is waiting, because it still has time to get home.
7 to 3
(0,4) down to (4,4)
6
SOUTH x5
Returns through the passage and down to row 5.
2 and 1
(5,4), (5,3)
6
WEST x2
Reaches the beach on the last step and lands 6 fish.

The two waiting steps are not a mistake. From the top of the reef the way home takes exactly 7 steps, and the tide only ever pushes south, which is toward home, so it can only help on the way back. Leaving earlier would land the same 6 fish, so the two choices have the same value and the policy keeps the first action in its list. It starts the trip home as soon as waiting would no longer be safe.
Results
Test
Fish per day
Ratio to angkol (2.49)
Official check on the 400 practice days (lagoon.py --compare)
5.963
2.395 (target 1.5)
20,000 days with seeds the logbook did not use (1001 to 21000)
5.959
2.393
200,000 days with other unseen seeds (100000 to 299999)
5.958
2.393
Lowest average over 300 random sets of 200 unseen days
5.875
2.36
Exact expected catch from the start, from the backward induction
5.9575
2.393

The simulated averages agree with the exact expected value, which confirms that the table and the simulator describe the same game. In a sample of 10,000 days, 9,726 landed a full hold of 6 fish, 189 landed 5, 56 landed 4, and 29 landed 3 or fewer.
How the solution was checked
The rules were checked against the simulator. The move function in main.py was compared with the simulator's own advance function on every combination of position, hold, action, bite and tide: 252 x 6 x 4 = 6,048 cases, with no differences.
The output file passes the format check. lagoon.check_policy_file reports no problems: correct header, 6,048 rows, every state once, only valid actions.
main.py works alone. It was run in a folder that contained only main.py and test-input.csv. It finished in about 0.09 seconds, far below the 60 second limit.
Allowed libraries only. The file imports only csv from the standard library. It contains no comments.
How to run it
Put main.py and train-input.csv in one folder, together with lagoon.py and train-output.json for the check.
Copy the practice input: cp train-input.csv test-input.csv
Run the agent: python main.py
Compare with angkol: python lagoon.py --policy test-output.csv --compare train-output.json
The last line should say that the ratio is above the target of 1.5. To watch one day step by step: python lagoon.py --policy test-output.csv --day 7
Glossary
Policy: a table that gives one action for every state.
State: everything the agent can see: row, column, fish in the hold and steps left.
Seed: the number that fixes all the random events of one day, so a day can be replayed exactly.
Expected value: the average result over all the ways the chance events could turn out, each weighted by its probability.
Dynamic programming (backward induction): solving a problem with steps over time by starting at the last step and working backwards, so that the value of every later situation is already known when an earlier one is evaluated.
Imitation: learning to copy the demonstrator's actions. It can match angkol but cannot go beyond his own strategy.
