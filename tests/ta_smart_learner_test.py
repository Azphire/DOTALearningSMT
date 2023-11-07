import unittest
import sys
sys.path.append("./")
from ta import buildTA, TAToDOT
from ta_smart_learner import learn_ta, generate_pair, compute_max_time
from equivalence import ota_equivalent
from pstats import Stats
import cProfile
import time
from statistics import mean


class SmartLearnerTest(unittest.TestCase):
    def testGen(self):
        test_cases = [
            [(), (0,), ((-1, 0), (-1, -1))],
            [(0,), (0,), ((-1, -1), (0, 0))],
            [(0,), (1,), ((-1, -1), (-1, 0), (0, -1), (0, 0))],
            [(0,), (0, 1), ((-1, -1), (-1, 1), (0, 0), (0, 1))],
            [(0, 1), (0, 1), ((-1, -1), (0, 0), (1, 1))],
            [(0,), (0, 1, 2), ((-1, -1), (-1, 1), (-1, 2), (0, 0), (0, 1), (0, 2))]
        ]

        for t1, t2, pairs in test_cases:
            res = generate_pair(t1, t2)
            self.assertEqual(len(res), len(pairs))
            self.assertEqual(set(res), set(pairs))

    def testLearnOTA(self):
        test_cases = [
            "DTA/a.json"
        ]

        profile = False
        graph = False

        if profile:
            pr = cProfile.Profile()
            pr.enable()

        with open("test_output.txt", "w") as output_file:
            locs = 0
            mems, eqs, timer = [], [], []
            trans_num = 0
            for f in test_cases:
                print("file name: %s", f)
                o = buildTA("../examples/%s" % f)
                trans_num += len(o.trans)
                start_time = time.perf_counter()
                learned_ta, mem_num, eq_num = learn_ta(o, verbose=False)
                end_time = time.perf_counter()
                timer.append(end_time - start_time)
                mems.append(mem_num)
                eqs.append(eq_num)
                loc = len(learned_ta.locations) - 1
                locs += loc
                output_file.write("Test %s: %.3f (s) Membership query: %d Equivalence query: %d Locations: %d\n" 
                            % (f, end_time - start_time, mem_num, eq_num, loc))
                output_file.flush()
                if graph:
                    TAToDOT(o, "ota_original")
                    TAToDOT(learned_ta, "ota_learned")
            output_file.write("Avg trans: %f mem: %f eq: %f loc:%f time:%f\n" % (trans_num/10, mean(mems), mean(eqs), locs/10, mean(timer)))
            output_file.write("MIN mem: %f eq: %f\n" % (min(mems), min(eqs)))
            output_file.write("MAX mem: %f eq: %f\n" % (max(mems), max(eqs)))

        if profile:
            p = Stats(pr)
            p.strip_dirs()
            p.sort_stats('cumtime')
            p.print_stats()

if __name__ == "__main__":
    unittest.main()
