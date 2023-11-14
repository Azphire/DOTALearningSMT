import pprint
from ta import Location, TimedWord, TA, TATran, buildAssistantTA, TAToJSON, TAToDOT
from interval import Interval
from equivalence import ota_equivalent
from equivalence_simple import OTAEquivalence
import copy
import z3
from os.path import commonprefix

from ta_equivalence import TAEquivalence

TT, TF, FT, FF = range(4)


def isSameRegion(t1: TimedWord, t2: TimedWord) -> bool:
    """Check whether t1 and t2 lies in the same region. That is,
    if they are equal, or if they are both non-integers in the same
    interval (n, n+1).

    """
    return t1 == t2 or (int(t1) != t1 and int(t2) != t2 and int(t1) == int(t2))


def start_diff_index(t1: TimedWord, t2: TimedWord) -> int:
    """Return the index from which prefix of 
    t1 and t2 become different"""
    return len(commonprefix([t1, t2]))


def generate_pair(t1: TimedWord, t2: TimedWord) -> tuple:
    """Generate all possible valid combination1
    of reset in t1 and t2.

    Input
      - t1, t2 :: tuple
    Output
      - a tuple of pairs
    """
    idx = start_diff_index(t1, t2)
    pairs = []
    # # Common prefix part
    # # 相同的前缀部分，最后一次重置信息应当是一样的
    # for ci in range(-1, idx):
    #     pairs.append((ci, ci))
    #     # t1: x |x| x o o
    #     # t2: x |x| x |o o o|
    #     # 在后续部分t2又有重置
    #     for di1 in range(idx, len(t2)):
    #         pairs.append((ci, di1))
    #     # t1: x |x| x |o o|
    #     # t2: x |x| x o o o
    #     # 在后续部分t1又有重置
    #     for di2 in range(idx, len(t1)):
    #         pairs.append((di2, ci))
    #
    # # Different prefix part
    # # t1: x x x |o| o
    # # t2: x x x |o o o|
    # for i in range(idx, len(t1)):
    #     for j in range(idx, len(t2)):
    #         pairs.append((i, j))

    # TODO：先整一个简单版，之后再优化
    for t1r1 in range(-1, len(t1)):
        for t1r2 in range(-1, len(t1)):
            for t2r1 in range(-1, len(t2)):
                for t2r2 in range(-1, len(t2)):
                    if t1r1 < idx and t2r1 < idx and t1r1 != t2r2:
                        pass
                    elif idx > t1r2 != t2r2 < idx:
                        pass
                    else:
                        pairs.append((t1r1, t1r2, t2r1, t2r2))

    return tuple(pairs)


def generate_t_reset(t: TimedWord, i: int, j: int) -> dict:
    reset = dict()
    min_ij = min(i, j)
    max_ij = max(i, j)
    reset[t[:min_ij + 1]] = (True, True)
    for k in range(i + 1, j + 1):
        reset[t[:k + 1]] = (False, True)
    for k in range(j + 1, i + 1):
        reset[t[:k + 1]] = (True, False)
    for k in range(max_ij + 1, len(t)):
        reset[t[:k + 1]] = (False, False)

    if tuple() in reset:
        del reset[tuple()]
    return reset


def generate_pair_resets(t1: TimedWord, t2: TimedWord, t1r1: int, t1r2: int, t2r1: int, t2r2: int) -> dict:
    reset = generate_t_reset(t1, t1r1, t1r2)
    reset.update(generate_t_reset(t2, t2r1, t2r2))
    # reset_t1r1, reset_t1r2, reset_t2r1, reset_t2r2 = dict(), dict(), dict(), dict()
    # reset_t1r1[t1[:t1r1 + 1]] = True
    # reset_t1r2[t1[:t1r2 + 1]] = True
    # reset_t2r1[t2[:t2r1 + 1]] = True
    # reset_t2r2[t2[:t2r2 + 1]] = True
    # for k in range(t1r1 + 1, len(t1)):
    #     reset_t1r1[t1[:k + 1]] = False
    # for k in range(t1r2 + 1, len(t1)):
    #     reset_t1r2[t1[:k + 1]] = False
    # for k in range(t2r1 + 1, len(t2)):
    #     reset_t2r1[t2[:k + 1]] = False
    # for k in range(t2r2 + 1, len(t2)):
    #     reset_t2r2[t2[:k + 1]] = False
    # if tuple() in reset_t1r1:
    #     del reset_t1r1[tuple()]
    # if tuple() in reset_t1r2:
    #     del reset_t1r2[tuple()]
    # if tuple() in reset_t2r1:
    #     del reset_t2r1[tuple()]
    # if tuple() in reset_t2r2:
    #     del reset_t2r2[tuple()]
    return reset


def generate_reset_rows(t1: TimedWord, t2: TimedWord) -> list:
    pairs = generate_pair(t1, t2)
    resets = []
    for t1r1, t1r2, t2r1, t2r2 in pairs:
        resets.append(generate_pair_resets(t1, t2, t1r1, t1r2, t2r1, t2r2))
    return resets


def generate_pair_resets_enhance(t1: TimedWord, t2: TimedWord, t1r1: int, t1r2: int, t2r1: int, t2r2: int,
                                 T1, T2) -> dict:
    prefix_reset = generate_pair_resets(t1[:-1], t2[:-1], t1r1, t1r2, t2r1, t2r2)
    if T1 == TT:
        prefix_reset[t1] = True, True
    elif T1 == TF:
        prefix_reset[t1] = True, False
    elif T1 == FT:
        prefix_reset[t1] = False, True
    elif T1 == FF:
        prefix_reset[t1] = False, False
    else:
        raise NotImplementedError
    if T2 == TT:
        prefix_reset[t2] = True, True
    elif T2 == TF:
        prefix_reset[t2] = True, False
    elif T2 == FT:
        prefix_reset[t2] = False, True
    elif T2 == FF:
        prefix_reset[t2] = False, False
    else:
        raise NotImplementedError
    return prefix_reset


class TestSequence:
    """Represents data for a single test sequence."""

    def __init__(self, tws: list[TimedWord], res: int):
        """Initialize data for a test sequence.

        tws - list(TimedWord)
        res - 1, 0, or -1, indicating accept, non-accept, and sink.

        Keeps a dictionary info, mapping suffixes to test results.

        """
        self.tws = tuple(tws)

        self.is_accept = (res == 1)
        self.is_sink = (res == -1)
        self.info = dict()

    def __str__(self):
        if self.is_accept:
            res = "Accept\n"
        elif self.is_sink:
            res = "Sink\n"
        else:
            res = "Non-accept\n"
        for tws, val in sorted(self.info.items()):
            res += '  %s: %.1f\n' % (','.join(str(tw) for tw in tws), val)
        return res

    def __repr__(self):
        return str(self)

    def testSuffix(self, ta: TA, tws2: TimedWord, shift=0):
        """Test the given timed words starting from self.

        tws2 - list(TimedWord): suffix to be appended.
        shift - additional time before appending suffix.

        """
        assert len(tws2) > 0, 'testSuffix: expect nonempty suffix.'
        if shift > 0:
            tws2 = (TimedWord(tws2[0].action, tws2[0].time + shift),) + tws2[1:]
        tws = tuple(self.tws + tws2)
        if tws2 not in self.info:
            self.info[tws2] = ta.runTimedWord(tws)

        return self.info[tws2]

    def getTimeVal(self, resets) -> tuple:
        """Given a choice of resets, find the value of time at the end.
        
        resets - dict(TimedWord, bool).
        Mapping from timed words to whether guessing a reset at its end.

        """
        cur_time0, cur_time1 = 0, 0
        for i, tw in reversed(list(enumerate(self.tws))):
            if resets[0][self.tws[:i + 1]]:
                break
            else:
                cur_time0 += tw.time
        for i, tw in reversed(list(enumerate(self.tws))):
            if resets[1][self.tws[:i + 1]]:
                break
            else:
                cur_time1 += tw.time
        return cur_time0, cur_time1


class Learner:
    """Represents the state of the learner."""

    def __init__(self, ta):
        self.ta = ta
        self.actions = ta.sigma

        # Store the comparision result of tw1 and tw2 on a 
        # given reset which is represented by a pair (i, j)
        self.cache = dict()

        # R stores sequences that are internal and at the boundary.
        self.R = dict()

        # S stores sequences which represent different states
        self.S = dict()

        # extra_S stores those rows that are not guaranteed to be different
        # from S, but are needed as representatives for some resets.
        self.extra_S = dict()

        # Mapping from rows to states variables
        self.state_name = dict()

        # Mapping from rows to resets and states name
        self.reset_name = dict()

        # List of discriminator sequences
        self.E = []

        # Store the formulas in constraint1:
        # - If two rows can be distinguished under a given reset, then that
        #   reset implies the state_name of the two rows are not the same.
        self.constraint1_formula = []
        self.constraint1_formula_num = 0

        # Store triples of the form (tw1, tw2, reset):
        # - The two rows tw1 and tw2 cannot be distinguished by the current
        #   suffixes, under the given reset.
        self.constraint1_triple = []

        # Store the formulas in constraint 2: 
        self.constraint2_formula = []
        self.constraint2_formula_num = 0

        # Store the formulas in constraint4: consistency
        self.constraint4_formula1 = []
        self.constraint4_formula2 = []
        self.constraint4_formula_num = 0
        # Store the (tw1, tw2, reset) triple in which both tw1[:-1] == tw2[:-1] and tw1 == tw2
        self.constraint4_triple1 = []

        # Store sink constraints
        self.sink_constraint = set()

        self.addPath(())

        # Count the number of occurrence
        self.formulas_count = dict()

        # Store the query result
        self.query_result = dict()

        # Incremental solver
        self.solver = z3.Solver()

        # Record the full constraint1
        self.full_constraint1 = []

    def __str__(self):
        res = 'R:\n'
        for twR, info in sorted(self.R.items()):
            res += str(twR) + ': ' + str(info)
        res += 'S:\n'
        for twS, info in sorted(self.S.items()):
            res += str(twS) + ': ' + str(info)
        res += 'S+:\n'
        for twS, info in sorted(self.extra_S.items()):
            res += str(twS) + ': ' + str(info)
        res += 'E:\n'
        res += '\n'.join(','.join(str(tw) for tw in twE) for twE in self.E)
        return res

    def find_row(self, row_name):
        """Find the row whose state is encoded as row_name"""
        for r in self.state_name:
            if self.state_name[r] == row_name:
                return r

    def addRow(self, tws, res):
        """When adding a new row, complete the corresponding information.
        
        Compare the new row with previous rows, find if there are new formulas on
        constriant1, constraint2, and constraint4.

        """
        # Create two z3 variables: r_n is a boolean variable for whether
        # there is reset following tws. s_n is an integer variable for
        # the assignment of the current state.
        self.reset_name[(tws, 1)] = z3.Bool("r_%d1" % len(self.R))  # reset1
        self.reset_name[(tws, 2)] = z3.Bool("r_%d2" % len(self.R))  # reset2
        self.state_name[tws] = z3.Int("s_%d" % len(self.R))
        sequence = TestSequence(tws, res)

        # Compare the new row with each of the existing rows. For each
        # existing row that can be distinguished from the new row under some
        # resets, add the corresponding constraint1. Otherwise, record the
        # inability to distinguish to constraint1_triple.
        for row in self.R:
            if not sequence.is_sink and not self.R[row].is_sink:  # 都不是sink
                if sequence.is_accept != self.R[row].is_accept:  # 成员查询结果不一样
                    self.constraint1_formula.append(self.state_name[row] != self.state_name[tws])  # 更新c1
                else:  # 成员查询结果一样
                    pairs = generate_pair(row, tws)
                    test_res = dict()
                    test_row = dict()
                    test_col = dict()
                    # Store test result in a matrix, which is convenient for 
                    # observing the result in one row (column)
                    for t1r1, t1r2, t2r1, t2r2 in pairs:
                        reset = generate_pair_resets(row, tws, t1r1, t1r2, t2r1, t2r2)
                        res = (self.findDistinguishingSuffix(self.R[row], sequence, reset, t1r1, t1r2, t2r1, t2r2)
                               is not None)
                        if (t1r1, t1r2) not in test_row:
                            test_row[(t1r1, t1r2)] = {(t2r1, t2r2): res}
                        else:
                            test_row[(t1r1, t1r2)][(t2r1, t2r2)] = res
                        if (t2r1, t2r2) not in test_col:
                            test_col[(t2r1, t2r2)] = {(t1r1, t1r2): res}
                        else:
                            test_col[(t2r1, t2r2)][(t1r1, t1r2)] = res
                        test_res[((t1r1, t1r2), (t2r1, t2r2))] = res
                    if all(res for _, res in test_res.items()):
                        self.constraint1_formula.append(self.state_name[row] != self.state_name[tws])
                    else:
                        # If all j can be distinguished by a specific i
                        for (t1r1, t1r2) in test_row:
                            if all(res for _, res in test_row[(t1r1, t1r2)].items()):
                                row_resets = generate_t_reset(row, t1r1, t1r2)
                                row_f = z3.Implies(self.encodeReset(row_resets, self.reset_name),
                                                   self.state_name[row] != self.state_name[tws])
                                self.constraint1_formula.append(row_f)

                                # Delete used pairs
                                for (t1r1_, t1r2_), (t2r1_, t2r2_) in list(test_res.keys()):
                                    if (t1r1_, t1r2_) == (t1r1, t1r2):
                                        del test_res[((t1r1_, t1r2_), (t2r1_, t2r2_))]
                        for (t2r1, t2r2) in test_col:
                            if all(res for _, res in test_col[(t2r1, t2r2)].items()):
                                col_reset = generate_t_reset(tws, t2r1, t2r2)
                                col_f = z3.Implies(self.encodeReset(col_reset, self.reset_name),
                                                   self.state_name[row] != self.state_name[tws])
                                self.constraint1_formula.append(col_f)
                                # spec_col.append(self.encodeReset(col_j_reset, self.reset_name))
                                for (t1r1_, t1r2_), (t2r1_, t2r2_) in list(test_res.keys()):
                                    if (t2r1_, t2r2_) == (t2r1, t2r2):
                                        del test_res[(t1r1_, t1r2_), (t2r1_, t2r2_)]
                        for ((t1r1, t1r2), (t2r1, t2r2)), res in test_res.items():
                            reset = generate_pair_resets(row, tws, t1r1, t1r2, t2r1, t2r2)  # 这里要怎么设置?
                            if res:
                                f = z3.Implies(self.encodeReset(reset, self.reset_name),
                                               self.state_name[row] != self.state_name[tws])
                                self.constraint1_formula.append(f)
                            else:
                                self.constraint1_triple.append((row, tws, reset, (t1r1, t1r2), (t2r1, t2r2)))

        new_Es = []
        for row in self.R:
            # For each existing row whose last action equals the new row.
            if row != () and tws != () and row[-1].action == tws[-1].action:
                pairs = generate_pair(row[:-1], tws[:-1])
                # possible_resets = generate_row_resets_enhance(row, tws)
                # for reset in possible_resets:
                for t1r1, t1r2, t2r1, t2r2 in pairs:
                    for b1 in range(4):
                        for b2 in range(4):
                            # reset = generate_row_resets_enhance1(row, tws, i, j, b)
                            reset = generate_pair_resets_enhance(row, tws, t1r1, t1r2, t2r1, t2r2, b1, b2)
                            if self.findDistinguishingSuffix(self.R[row[:-1]], self.R[tws[:-1]], reset,
                                                             t1r1, t1r2, t2r1, t2r2) is None:
                                time_vals1 = self.R[row[:-1]].getTimeVal(reset)
                                time_vals2 = self.R[tws[:-1]].getTimeVal(reset)
                                if isSameRegion(time_vals1[0] + row[-1].time, time_vals2[0] + tws[-1].time) and \
                                        isSameRegion(time_vals1[1] + row[-1].time, time_vals2[1] + tws[-1].time):
                                    f = z3.Implies(self.state_name[row[:-1]] == self.state_name[tws[:-1]],
                                                   z3.Not(self.encodeReset(reset, self.reset_name)))
                                    # If reached the same time region, then the two states being the same
                                    # implies the two resets must be the same. Add the corresponding formula
                                    # to constraint2, and record the information in constraint2_triple.
                                    if reset[row] != reset[tws]:
                                        self.constraint2_formula.append(f)
                                        continue

                                    suffix = self.findDistinguishingSuffix(self.R[row], sequence, reset,
                                                                           t1r1, t1r2, t2r1, t2r2, bb=(b1, b2))
                                    # If row[:-1] and tws[:-1] are not distinguishable by the current suffixes,
                                    # but row and tws are distinguishable, add new suffix to E. Also add the
                                    # constraint excluding row[:-1] and tws[:-1] being the same state under the
                                    # given reset.
                                    # Constraint4_formula1: It means that if tws[:-1] and rows[:-1] are at the
                                    # same state, tws and rows are also supposed to at the same state under
                                    # current reset, if not, the reset is invalid.
                                    if suffix is not None:
                                        self.constraint4_formula1.append(f)
                                        # May become different after adding some suffixes
                                        suffix = (TimedWord(row[-1].action, min(row[-1].time, tws[-1].time)),) + suffix
                                        new_Es.append(suffix)

                                    # If row and tws are also not distinguishable, add a constraint saying
                                    # if row[:-1] and tws[:-1] are mapped to the same state, then under the
                                    # given reset row and tws are also mapped to the same reset.
                                    else:
                                        f2 = z3.Implies(z3.And(self.state_name[row[:-1]] == self.state_name[tws[:-1]],
                                                               self.encodeReset(reset, self.reset_name)),
                                                        self.state_name[row] == self.state_name[tws])
                                        self.constraint4_formula2.append(f2)
                                        # E is increasing, row and tws are possible to be distinguished in t future,
                                        # so store (row, tws, reset) in constraint4_triple1
                                        self.constraint4_triple1.append((row, tws, reset, (t1r1, t1r2), (t2r1, t2r2),
                                                                         (b1, b2)))

        # Add a new timed word to R.
        self.R[tws] = sequence

        # Add each new suffix.
        for e in new_Es:
            self.addSuffix(e)

    def addSuffix(self, suffix):
        """When adding a suffix, we can check if some pairs of tws can be
        distinguished now, new formulas can be added in constraint1 or constraint4.

        Check if there are rows in R that can be distinguished from all existing
        rows in S, and if so add them to S.

        """
        if suffix in self.E:
            return

        # Add new formulas to constraint1.
        self.E.append(suffix)
        delete_items = []
        for tw1, tw2, reset, (t1r1, t1r2), (t2r1, t2r2) in self.constraint1_triple:
            if self.findDistinguishingSuffix(self.R[tw1], self.R[tw2], reset, t1r1, t1r2, t2r1, t2r2, suffix) \
                    is not None:
                f = z3.Implies(self.encodeReset(reset, self.reset_name),
                               self.state_name[tw1] != self.state_name[tw2])
                self.constraint1_formula.append(f)
                delete_items.append((tw1, tw2, reset, (t1r1, t1r2), (t2r1, t2r2)))

        for t in delete_items:
            self.constraint1_triple.remove(t)

        # Re-test condition for adding to constraint4_formula1. Should add to new_Es?
        delete_items = []
        for tw1, tw2, reset, (t1r1, t1r2), (t2r1, t2r2), (b1, b2) in self.constraint4_triple1:
            if self.findDistinguishingSuffix(self.R[tw1[:-1]], self.R[tw2[:-1]], reset,
                                             t1r1, t1r2, t2r1, t2r2, suffix) is None:
                time_vals1 = self.R[tw1[:-1]].getTimeVal(reset)
                time_vals2 = self.R[tw2[:-1]].getTimeVal(reset)
                if isSameRegion(time_vals1[0] + tw1[-1].time, time_vals2[0] + tw2[-1].time) and \
                        isSameRegion(time_vals1[1] + tw1[-1].time, time_vals2[1] + tw2[-1].time):
                    s = self.findDistinguishingSuffix(self.R[tw1], self.R[tw2], reset, t1r1, t1r2, t2r1, t2r2, suffix,
                                                      (b1, b2))
                    if s is not None:
                        f = z3.Implies(self.state_name[tw1[:-1]] == self.state_name[tw2[:-1]],
                                       z3.Not(self.encodeReset(reset, self.reset_name)))
                        self.constraint4_formula1.append(f)
                        delete_items.append((tw1, tw2, reset, (t1r1, t1r2), (t2r1, t2r2), (b1, b2)))

        for t in delete_items:
            self.constraint4_triple1.remove(t)

        # Check if some state in R can be added to S. A state in R can be
        # added to S if it is different from all existing rows in S under
        # all possible resets.
        delete_items = []
        for tw1 in self.R:
            if tw1 in self.S:
                continue
            is_new_state = True
            for tw2 in list(self.S.keys()) + delete_items:
                # possible_resets = generate_reset_rows(tw1, tw2)
                # for reset in possible_resets:
                for t1r1, t1r2, t2r1, t2r2 in generate_pair(tw1, tw2):
                    reset = generate_pair_resets(tw1, tw2, t1r1, t1r2, t2r1, t2r2)
                    if self.findDistinguishingSuffix(self.R[tw1], self.R[tw2], reset, t1r1, t1r2, t2r1, t2r2, suffix) \
                            is None:
                        is_new_state = False

                if not is_new_state:
                    break

            if is_new_state:
                delete_items.append(tw1)

        # Add state from R into S.
        for tws in delete_items:
            if self.checkNewState(tws) and self.ta.runTimedWord(tws) != -1:
                self.addToS(tws)

    def addToS(self, tws):
        """Add a new row to S. This also requires adding the row followed by
        (act, 0) for each action a into R.
        
        """
        assert tws in self.R and tws not in self.S, \
            "addToS: tws should be in R and not in S"
        self.S[tws] = self.R[tws]

        if self.ta.runTimedWord(tws) != -1:
            for act in self.actions:
                cur_tws = tws + (TimedWord(act, 0),)
                if cur_tws not in self.R:
                    self.addPath(cur_tws)

    def addPossibleS(self, tws):
        """Check if tws can be added into S. If not, add
        tws + (act, 0) for each action into R.
        
        """
        if self.checkNewState(tws):
            # Distinct from all states in S, directly add to S
            self.addToS(tws)
        else:
            # Otherwise, add to extra_S
            self.extra_S[tws] = self.R[tws]
            for act in self.actions:
                new_tws = tws + (TimedWord(act, 0),)
                new_res = self.ta.runTimedWord(new_tws)
                if new_tws not in self.R:
                    self.addRow(new_tws, new_res)

    def addPath(self, tws):
        """Add the given path tws (and its prefixes) to R.
        
        Starting from the head, it keeps adding longer prefixes until reaching
        the sink.

        """
        tws = tuple(tws)
        assert tws not in self.R, "Redundant R: %s" % str(tws)
        for i in range(len(tws) + 1):
            cur_tws = tws[:i]
            cur_res = self.ta.runTimedWord(cur_tws)
            if cur_tws not in self.R:
                self.addRow(cur_tws, cur_res)
                is_new_state = self.checkNewState(cur_tws)

                if is_new_state and cur_tws not in self.S and cur_res != -1:
                    self.addToS(cur_tws)

            if cur_res == -1:
                break

    def checkNewState(self, tws):
        """Check if tw is different from any other rows in S."""
        if tws in self.S:
            return False

        sequence = self.R[tws]
        for row in self.S:
            if row != tws:
                # resets = generate_reset_rows(row, tws)
                pairs = generate_pair(row, tws)
                for t1r1, t1r2, t2r1, t2r2 in pairs:
                    # for reset in resets:
                    reset = generate_pair_resets(row, tws, t1r1, t1r2, t2r1, t2r2)
                    if self.findDistinguishingSuffix(self.R[row], sequence, reset, t1r1, t1r2, t2r1, t2r2) is None:
                        return False

        return True

    def findDistinguishingSuffix(self, info1, info2, resets, t1r1, t1r2, t2r1, t2r2, E=None, bb=None):
        """Check whether the two timed words are equivalent.
        
        If equivalent according to the current E, return None.

        Otherwise, return the distinguishing suffix (which works by shifting
        the first timed word to align the clock).

        """
        if bb is None:
            if (info1, info2) in self.cache and E is None:
                if (t1r1, t1r2, t2r1, t2r2) in self.cache[(info1, info2)]:
                    return self.cache[(info1, info2)][(t1r1, t1r2, t2r1, t2r2)]
            else:
                self.cache[(info1, info2)] = dict()
        else:
            if (info1, info2) in self.cache and E is None:
                if (t1r1, t1r2, t2r1, t2r2, bb) in self.cache[(info1, info2)]:
                    return self.cache[(info1, info2)][(t1r1, t1r2, t2r1, t2r2, bb)]
            else:
                self.cache[(info1, info2)] = dict()

        if info1.is_accept != info2.is_accept or info1.is_sink != info2.is_sink:
            return tuple()  # empty suffix is distinguishing

        time1 = info1.getTimeVal(resets)
        time2 = info2.getTimeVal(resets)

        if E is None:
            suffix = self.E
        else:
            suffix = [E]

        res = None
        for twE in suffix:
            if time1 == time2:
                res1 = info1.testSuffix(self.ta, twE)
                res2 = info2.testSuffix(self.ta, twE)
            elif time1 < time2:
                shift = time2 - time1
                res1 = info1.testSuffix(self.ta, twE, shift)
                res2 = info2.testSuffix(self.ta, twE)
            else:  # time1 > time2
                shift = time1 - time2
                res1 = info1.testSuffix(self.ta, twE)
                res2 = info2.testSuffix(self.ta, twE, shift)
            if res1 != res2:
                res = twE
                break

        if bb is None:
            self.cache[(info1, info2)][(t1r1, t1r2, t2r1, t2r2)] = res
        else:
            self.cache[(info1, info2)][(t1r1, t1r2, t2r1, t2r2, bb)] = res
        return res

    def encodeReset(self, reset: dict, resets_var: dict):
        """Encode the reset information into formula.
        
        Note: the formula only contains rows which start from the last reset.
        Example: suppose a sequence
        (a, t1, ⊥)(b, t2, ⊥)(c, t3, ⊤)(d, t4, ⊤)
        then the formula only contains the variables which represent
        r_3: (a, t1, ⊥)(b, t2, ⊥)(c, t3, ⊤),
        r_4: (a, t1, ⊥)(b, t2, ⊥)(c, t3, ⊤)(d, t4, ⊤)
        since (a, t1) and (a, t1)(b, t2) 's reset cannot influence the whole time.
        """
        formula = []
        for row, r1, r2 in reset.items():
            if r1:
                formula.append(resets_var[row][0])
            else:
                formula.append(z3.Not(resets_var[row][0]))
            if r2:
                formula.append(resets_var[row][1])
            else:
                formula.append(z3.Not(resets_var[row][1]))
        assert len(formula) > 0, "Invalid resets!"
        return z3.And(formula)

    def differentStateUnderReset(self):
        """Constraint 1: if two rows can be distinguished under a reset, then they
        cannot be mapped to the same state.

        """
        return self.constraint1_formula

    def noForbiddenPair(self):
        """Constraint 2: for any tow rows R1 + (a, t1) and R2 + (a, t2), 
        if states[R1] = states[R2], and they are in the same time interval,
        then they should have same reset settings.

        """
        return self.constraint2_formula

    def checkConsistency(self):
        """Constraint 4: for any two rows R1 + (a, t1), R2 + (a, t2). If R1 and R2 are
        in the same states, and under the current reset settings these two rows are in
        the same time interval, then their states should also be same.
        
        """
        return self.constraint4_formula1 + self.constraint4_formula2

    def setSinkRowReset(self):
        """Constraint 5: All sink rows's resets are set to True."""
        formulas = []
        for r, info in self.R.items():
            if info.is_sink:
                # if r not in self.sink_constraint:
                #     self.sink_constraint.add(r)
                formulas.append(self.reset_name[(r, 1)] == True)
                formulas.append(self.reset_name[(r, 2)] == True)

        return formulas

    def encodeSRow(self):
        """Each row in S should have a unique state."""
        formulas = []
        for i, s in enumerate(self.S):
            formulas.append(self.state_name[s] == (i + 1))

        return formulas

    def encodeStateNum(self, state_num):
        """The state name of each row must be between 1 and state_num, except the
        sink states, which must have state_num equal to state_num + 1.
        
        """
        formulas = []
        for row, s in self.state_name.items():
            if self.R[row].is_sink:
                formulas.append(s == state_num + 1)
            else:
                formulas.append(s >= 1)
                formulas.append(s <= state_num)

        return formulas

    def encodeExtraS(self, state_num):
        """The states in extra_S must cover all remaining state_num."""
        formulas = []
        for i in range(len(self.S) + 1, state_num + 1):
            formulas.append(z3.Or(*(self.state_name[row] == i for row in self.extra_S)))

        return formulas

    def clearConstraint(self):
        self.constraint1_formula_num += len(self.constraint1_formula)
        self.full_constraint1 += self.constraint1_formula
        self.constraint1_formula = []
        self.constraint2_formula_num += len(self.constraint2_formula)
        self.constraint2_formula = []
        self.constraint4_formula_num += \
            len(self.constraint4_formula1) + len(self.constraint4_formula2)
        self.constraint4_formula1 = []
        self.constraint4_formula2 = []

    def display_formula(self):
        print("display formula")
        d = dict()
        for f in self.full_constraint1:
            if z3.is_implies(f):
                imp = f.arg(1)
                reset_encoding = f.arg(0)
                r1, r2 = imp.children()
                if (r1, r2) not in d:
                    d[(r1, r2)] = [reset_encoding]
                else:
                    d[(r1, r2)].append(reset_encoding)
            else:
                r1, r2 = f.children()
                d[(r1, r2)] = [False]
        for r1, r2 in d:
            print("row_1", r1, self.find_row(r1))
            print("row_2", r2, self.find_row(r2))
            print(z3.Or(*d[(r1, r2)]))
            print()

    def findReset(self, state_num, enforce_extra):
        """Find a valid setting of resets and states.
        
        state_num - number of locations in the automata.
        enforce_extra - whether to enforce the condition that all rows have a
            representative in S or extra_S.
            
        Return a tuple (resets, states). 

        """
        constraint1 = self.differentStateUnderReset()
        constraint2 = self.noForbiddenPair()
        constraint4 = self.checkConsistency()
        constraint5 = self.setSinkRowReset()
        constraint7 = self.encodeSRow()

        assert state_num >= len(self.S)
        constraint6 = self.encodeStateNum(state_num)
        if enforce_extra:
            constraint8 = self.encodeExtraS(state_num)
        else:
            constraint8 = []

        print("%d %d %d\n" % (self.constraint1_formula_num,
                              self.constraint2_formula_num, self.constraint4_formula_num))
        self.solver.push()
        self.solver.add(*(constraint1 + constraint2 + constraint4 + constraint5))
        self.solver.push()
        self.solver.add(*(constraint6 + constraint7 + constraint8))

        if str(self.solver.check()) == "unsat":
            # No assignment can be found for current S, extra_S, and state_num
            self.solver.pop()
            return None, None, None

        # An assignment is found, construct resets and states from the model.
        model = self.solver.model()
        self.solver.pop()
        self.clearConstraint()
        resets1, resets2, states = dict(), dict(), dict()

        for row in self.R:
            states[row] = str(model[self.state_name[row]])
            resets1[row] = bool(model[self.reset_name[(row, 1)]])
            resets2[row] = bool(model[self.reset_name[(row, 2)]])

        states["sink"] = str(state_num + 1)

        return resets1, resets2, states

    def buildCandidateOTA(self, resets, states):
        """Construct candidate OTA from current information.

        resets - guessed reset information for each entry in R.
        states - guessed state mapping for each entry in R.

        """
        states_num = int(states["sink"])

        # Mapping from location, action and time to transitions,
        # in the form of (reset, target)
        # transitions: states -> action -> time -> (reset, state)
        transitions = dict()
        for i in range(states_num):
            name = str(i + 1)
            transitions[name] = dict()
            for act in self.actions:
                transitions[name][act] = dict()

        # List of accept states
        accepts = set()
        for row in states:
            if row != 'sink' and self.R[row].is_accept:
                accepts.add(states[row])

        accepts = list(accepts)
        # Fill in transitions using R.
        for twR in sorted(self.R):
            if twR == ():
                continue

            prev_loc = states[twR[:-1]]
            start_time = self.R[twR[:-1]].getTimeVal(resets)
            trans_time = (start_time[0] + twR[-1].time, start_time[1] + twR[-1].time)
            if self.R[twR].is_sink:
                cur_reset, cur_loc = (True, True), states['sink']
            else:
                cur_reset, cur_loc = (resets[0][twR], resets[1][twR]), states[twR]

            if trans_time in transitions[prev_loc][twR[-1].action] and \
                    (cur_reset, cur_loc) != transitions[prev_loc][twR[-1].action][trans_time]:
                print('When adding transition for', twR)
                raise AssertionError('Conflict at %s (%s, %s)' % (prev_loc, twR[-1].action, trans_time))
            transitions[prev_loc][twR[-1].action][trans_time] = cur_reset, cur_loc

        # Sink transitions
        for act in self.actions:
            transitions[states["sink"]][act][(0, 0)] = ((True, True), states["sink"])

        # From the dictionary of transitions, form the list otaTrans
        otaTrans = []
        for source in transitions:
            for action, trans in transitions[source].items():
                # Sort and remove duplicates
                trans = sorted((time, reset, target) for time, (reset, target) in trans.items())
                # If the first transition is not zero, add transition to sink
                if trans[0][0] != (0, 0):
                    trans = [((0, 0), True, states["sink"])] + trans

                trans_new = [trans[0]]
                for i in range(1, len(trans)):
                    time, reset, target = trans[i]
                    prev_time, prev_reset, prev_target = trans[i - 1]
                    if reset != prev_reset or target != prev_target:
                        trans_new.append(trans[i] )
                trans = trans_new

                # Change to otaTrans.
                # TODO: 双时钟的区间怎么生成
                for i in range(len(trans)):
                    time, reset, target = trans[i]
                    if int(time) == time:
                        min_value, closed_min = int(time), True
                    else:
                        min_value, closed_min = int(time), False
                    if i < len(trans) - 1:
                        time2, reset2, target2 = trans[i + 1]
                        if int(time2) == time2:
                            max_value, closed_max = int(time2), False
                        else:
                            max_value, closed_max = int(time2), True
                        constraint = Interval(min_value, closed_min, max_value, closed_max)
                    else:
                        constraint = Interval(min_value, closed_min, '+', False)
                    otaTrans.append(TATran(source, action, constraint, reset, target))

        # Form the location objects
        location_objs = set()
        for tw, loc in states.items():
            if tw == "sink":
                location_objs.add(Location(loc, False, False, True))
            else:
                location_objs.add(Location(loc, (loc == "1"), self.R[tw].is_accept, self.R[tw].is_sink))

        candidateTA = TA(
            name=self.ta.name + '_',
            sigma=self.actions,
            locations=location_objs,
            trans=otaTrans,
            init_state='1',
            accept_states=accepts,
            sink_name=states['sink'])

        return True, candidateTA


def compute_max_time(candidate):
    def parse_time(t):
        return 0 if t == "+" else int(t)

    max_time = 0
    for tran in candidate.trans:
        max_time = max(max_time,
                       parse_time(tran.constraints[0].min_value),
                       parse_time(tran.constraints[1].min_value),
                       parse_time(tran.constraints[0].max_value),
                       parse_time(tran.constraints[1].max_value))
    return max_time


def learn_ta(ta, verbose=True, graph=False):
    """Overall learning loop.
    
    verbose - whether to print debug information.

    """
    print("Start to learn ta %s.\n" % ta.name)
    learner = Learner(ta)
    assist_ta = buildAssistantTA(ta)
    max_time_ta = compute_max_time(ta)
    state_num = 1
    eq_query_num = 0
    step = 0
    while True:
        step += 1
        print("Step", step)

        # If size of S has increased beyond state_num, adjust state_num to
        # that size.
        if state_num < len(learner.S):
            state_num = len(learner.S)
            print("Adjust state_num to len(S) = %s" % state_num)

        print("#S = %d, #extra_S = %d, state_num = %d, #R = %d, #R (no sink) = %d" % (
            len(learner.S), len(learner.extra_S), state_num, len(learner.R),
            len([row for row, s in learner.R.items() if not s.is_sink])
        ))

        # First, try with current state_num and enforce the constraint
        # that all representatives are in extra_S.
        resets1, resets2, states = learner.findReset(state_num, True)

        # If fails, try again without the constraint that all representatives
        # are in extra_S. Add any new representative to extra_S.
        if resets1 is None:
            resets1, resets2, states = learner.findReset(state_num, False)

            # If still not found, must increase state_num.
            if resets1 is None:
                state_num += 1
                print("Increment state_num to %s." % state_num)
                continue

            # Otherwise, add new representatives to extra_S.
            has_reps = dict()
            for i in range(1, state_num + 1):
                has_reps[i] = False
            for row in learner.S:
                has_reps[int(states[row])] = True
            for row in learner.extra_S:
                has_reps[int(states[row])] = True

            new_reps = []
            for row in learner.R:
                if int(states[row]) <= state_num and not has_reps[int(states[row])]:
                    has_reps[int(states[row])] = True
                    new_reps.append(row)
            assert len(new_reps) > 0

            for rep in new_reps:
                print("Add %s to extra_S." % str(rep))
                learner.addPossibleS(rep)
            continue

        if verbose:
            print(learner)

        if resets1 is None:
            # Should not arrive here
            raise AssertionError

        if verbose:
            print("resets and states:")
            for tws, v in resets1.items():
                print("  %s: %s %s" % (",".join(str(tw) for tw in tws), v, states[tws]))
            for tws, v in resets2.items():
                print("  %s: %s %s" % (",".join(str(tw) for tw in tws), v, states[tws]))

        f, candidate = learner.buildCandidateOTA((resets1, resets2), states)
        if not f:
            raise AssertionError("buildCandidateOTA failed.")

        max_time_candidate = compute_max_time(candidate)
        max_time = max(max_time_ta, max_time_candidate)

        ta_equiv = TAEquivalence(max_time, assist_ta, candidate)
        res, ctx_path = ta_equiv.eq_query()

        # res, ctx = ota_equivalent(max_time, assist_ota, candidate)
        eq_query_num += 1
        if not res and verbose:
            print(candidate)
        if res:
            print(candidate)
            print("Finished in %s steps " % step)
            return candidate, len(ta.query), eq_query_num
        if graph:
            TAToDOT(candidate, "Step %d" % step)
        if verbose:
            print("Counterexample", ctx_path, ta.runTimedWord(ctx_path), candidate.runTimedWord(ctx_path))
        learner.addPath(ctx_path)
