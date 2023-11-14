from ta import Location, TA, TimedWord, TATran
from interval import Interval


class TAEquivalence:

    def __init__(self, ta1: TA, ta2: TA, max_value):
        self.ta1 = ta1
        self.ta2 = ta2
        self.max_value = max_value
        self.explored = []  # clocks 和 locations
        self.to_explore = []  # 时间字

    def generate_relay(self, c1, c2, location1, location2, action: str) -> list:
        relay_list = []
        for trans in self.ta1.trans_dict[(action, location1)]:
            # 每个region左右生成一个relay，即guard时间减去现在时间
            if trans.constrains[0].min_value - c1[0] >= 0:
                if trans.constrains[0].closed_min:
                    relay_list.append(trans.constrains[0].min_value - c1[0])
                else:
                    relay_list.append(trans.constrains[0].min_value - c1[0] + 0.5)
            if trans.constrains.max_value - c1[0] >= 0:
                if self.max_value in trans.constrains[0]:
                    pass
                elif trans.constrains[0].closed_max:
                    relay_list.append(trans.constrains[0].max_value - c1[0])
                elif trans.constrains[0].max_value - c1[0] > 0:
                    relay_list.append(trans.constrains[0].max_value - c1[0] - 0.5)
            if trans.constrains[1].min_value - c1[1] >= 0:
                if trans.constrains[1].closed_min:
                    relay_list.append(trans.constrains[1].min_value - c1[1])
                else:
                    relay_list.append(trans.constrains[1].min_value - c1[1] + 0.5)
            if trans.constrains.max_value - c1[1] >= 0:
                if self.max_value in trans.constrains[1]:
                    pass
                elif trans.constrains[1].closed_max:
                    relay_list.append(trans.constrains[1].max_value - c1[1])
                elif trans.constrains[1].max_value - c1[1] > 0:
                    relay_list.append(trans.constrains[1].max_value - c1[1] - 0.5)

        for trans in self.ta2.trans_dict[(action, location2)]:
            # 每个region左右生成一个relay，即guard时间减去现在时间
            if trans.constrains[0].min_value - c2[0] >= 0:
                if trans.constrains[0].closed_min:
                    relay_list.append(trans.constrains[0].min_value - c2[0])
                else:
                    relay_list.append(trans.constrains[0].min_value - c2[0] + 0.5)
            if trans.constrains.max_value - c2[0] >= 0:
                if self.max_value in trans.constrains[0]:
                    pass
                elif trans.constrains[0].closed_max:
                    relay_list.append(trans.constrains[0].max_value - c2[0])
                elif trans.constrains[0].max_value - c2[0] > 0:
                    relay_list.append(trans.constrains[0].max_value - c2[0] - 0.5)
            if trans.constrains[1].min_value - c2[1] >= 0:
                if trans.constrains[1].closed_min:
                    relay_list.append(trans.constrains[1].min_value - c2[1])
                else:
                    relay_list.append(trans.constrains[1].min_value - c2[1] + 0.5)
            if trans.constrains.max_value - c2[1] >= 0:
                if self.max_value in trans.constrains[1]:
                    pass
                elif trans.constrains[1].closed_max:
                    relay_list.append(trans.constrains[1].max_value - c2[1])
                elif trans.constrains[1].max_value - c2[1] > 0:
                    relay_list.append(trans.constrains[1].max_value - c2[1] - 0.5)

        relay_list = list(set(relay_list))
        return relay_list

    def generate_tws(self, ta1_clocks, ta2_clocks, ta1_location, ta2_location) -> list:
        tws = []
        for a in self.ta1.sigma:
            relay_list = self.generate_relay(ta1_clocks, ta2_clocks, ta1_location, ta2_location, a)
            for relay in relay_list:
                tws.append((a, relay))
        return tws

    def explore(self, current_tw: list, ta1_clocks, ta2_clocks, ta1_location, ta2_location):
        self.explored.append((ta1_clocks, ta2_clocks, ta1_location, ta2_location))
        # 搜索所有状态，查看有没有返回不同的，遇到重复的location+clocks组合或者clocks都超过max value就停止
        tw_list = self.generate_tws(ta1_clocks, ta2_clocks, ta1_location, ta2_location)
        for tw in tw_list:
            ta1_target, ta1_resets = self.ta1.runTransition(ta1_clocks, tw[1], ta1_location, tw[0])
            ta2_target, ta2_resets = self.ta2.runTransition(ta2_clocks, tw[1], ta2_location, tw[0])
            ta1_1 = 0 if ta1_resets[0] else ta1_clocks[0] + tw[1]
            ta1_2 = 0 if ta1_resets[1] else ta1_clocks[1] + tw[1]
            ta2_1 = 0 if ta2_resets[0] else ta2_clocks[0] + tw[1]
            ta2_2 = 0 if ta2_resets[1] else ta2_clocks[1] + tw[1]
            if ((ta1_1, ta1_2), (ta2_1, ta2_2), ta1_target, ta2_target) in self.explored:
                pass
            else:
                if ta1_target in self.ta1.accept_states and ta2_target not in self.ta2.accept_states or \
                        ta1_target not in self.ta1.accept_states and ta2_target in self.ta2.accept_states:
                    return True, current_tw + [TimedWord(tw[0], tw[1])]
                elif ta1_target == self.ta1.sink_name and ta2_target == self.ta2.sink_name:
                    # 都是sink状态就不用继续往下explore了
                    self.explored.append(((ta1_1, ta1_2), (ta2_1, ta2_2), ta1_target, ta2_target))
                else:
                    # explore
                    self.to_explore.append((current_tw + [TimedWord(tw[0], tw[1])],
                                            ((ta1_1, ta1_2), (ta2_1, ta2_2), ta1_target, ta2_target)))
        return False, None

    def eq_query(self):
        is_ctx, tw = self.explore([], (0, 0), (0, 0), self.ta1.init_state, self.ta2.init_state)
        if is_ctx:
            return False, tw
        while len(self.to_explore) > 0:
            for tw, state in self.to_explore:
                is_ctx, new_tw = self.explore(tw, state[0], state[1], state[2], state[3])
                if is_ctx:
                    return False, new_tw
                self.to_explore.remove((tw, state))
        return True, None
