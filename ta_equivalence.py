from ta import Location, TA, TimedWord, TATran
from interval import Interval


class TAEquivalence:

    def __init__(self, ta1: TA, ta2: TA, max_value):
        self.ta1 = ta1
        self.ta2 = ta2
        self.max_value = max_value
        self.explored = []
        self.to_explore = []

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
                if trans.constrains[0].closed_max:
                    relay_list.append(trans.constrains[0].max_value - c1[0])
                elif trans.constrains[0].max_value - c1[0] > 0:
                    relay_list.append(trans.constrains[0].max_value - c1[0] - 0.5)
            if trans.constrains[1].min_value - c1[1] >= 0:
                if trans.constrains[1].closed_min:
                    relay_list.append(trans.constrains[1].min_value - c1[1])
                else:
                    relay_list.append(trans.constrains[1].min_value - c1[1] + 0.5)
            if trans.constrains.max_value - c1[1] >= 0:
                if trans.constrains[1].closed_max:
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
                if trans.constrains[0].closed_max:
                    relay_list.append(trans.constrains[0].max_value - c2[0])
                elif trans.constrains[0].max_value - c2[0] > 0:
                    relay_list.append(trans.constrains[0].max_value - c2[0] - 0.5)
            if trans.constrains[1].min_value - c2[1] >= 0:
                if trans.constrains[1].closed_min:
                    relay_list.append(trans.constrains[1].min_value - c2[1])
                else:
                    relay_list.append(trans.constrains[1].min_value - c2[1] + 0.5)
            if trans.constrains.max_value - c2[1] >= 0:
                if trans.constrains[1].closed_max:
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

    def explore(self, ta1_clocks, ta2_clocks, ta1_location, ta2_location):
        # TODO:搜索所有状态，查看有没有返回不同的，遇到重复的location+clocks组合或者clocks都超过max value就停止
        tw_list = self.generate_tws(ta1_clocks, ta2_clocks, ta1_location, ta2_location)
        for tw in tw_list:
            ta1_target, ta1_resets = self.ta1.runTransition(ta1_clocks, tw[1], ta1_location, tw[0])
            ta2_target, ta2_resets = self.ta2.runTransition(ta2_clocks, tw[1], ta2_location, tw[0])
            # TODO：比较是否不同
        pass

    def start_explore(self):
        self.explore((0, 0), (0, 0), self.ta1.init_state, self.ta2.init_state)
