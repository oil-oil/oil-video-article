"""验证工程剪辑映射边界，禁止越界时间静默返回最后一帧。"""
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
from extract_frame import map_time

class TimelineTests(unittest.TestCase):
    def test_speed_and_session_mapping(self):
        slices = [(0, 0, 1000, 3000, 2), (1000, 1, 5000, 6000, 1)]
        self.assertEqual(map_time(slices, 500), (0, 2000))
        self.assertEqual(map_time(slices, 1000), (1, 5000))
    def test_invalid_times_are_rejected(self):
        for time in (-1, 2000, float('nan'), float('inf')):
            with self.subTest(time=time), self.assertRaises(ValueError):
                map_time([(0,0,0,2000,1)], time)

if __name__ == '__main__': unittest.main()
