from ta import Location, TA, TimedWord
from interval import Interval

class TAEquivalence:

    def __init__(self, ta1: TA, ta2: TA, max_value):
        self.ta1 = ta1
        self.ta2 = ta2
        self.max_value = max_value
        self.explored = []
        self.to_explore = []

    def split_relay(self, explore_ta1: bool, c1, c2, location, action: str):
        relay_list = []
        if explore_ta1:
            for trans in self.ta1.trans_dict[(action, location)]:
                # TODO: 每个region左右生成一个relay

                pass
        else:
            pass
        return relay_list

    def generate_to_explore(self, ta1_clocks, ta2_clocks, ta1_location, ta2_location, explore_ta1: bool):
        if explore_ta1:
            # 划分待生成ta的region


            pass
        else:
            pass

        pass
