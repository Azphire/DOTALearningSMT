# Unit test for TA

import unittest
import sys
sys.path.append("./")
from ta import TimedWord, buildTA, buildAssistantTA


class OTATest(unittest.TestCase):
    def testBuildTA(self):
        ta = buildTA('../examples/DTA/a.json')
        assist_ta = buildAssistantTA(ta)
        print(ta)
        print(assist_ta)

    def testRunTimedWord(self):
        ta = buildTA('../examples/DTA/a.json')
        assist_ta = buildAssistantTA(ta)
        test_data = [
            # ([()], 0),
            ([('a', 1)], 0),
            ([('a', 1), ('b', 1)], 1),
            ([('a', 0)], -1),
        ]
        for tws, res in test_data:
            tws = tuple([TimedWord(action, time) for action, time in tws])
            self.assertEqual(ta.runTimedWord(tws), res)
            self.assertEqual(assist_ta.runTimedWord(tws), res)


if __name__ == "__main__":
    unittest.main()
