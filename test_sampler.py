"""test_sampler - some unit tests for the sampler module"""

import time
import unittest
from lib.sampler import sampler


class TestSampler(unittest.TestCase):

    def test_reset(self):
        """Test initialization and reset() method"""
        samples = sampler(10)

        # There should be no recorded samples
        last_sample = samples.last()
        self.assertEqual(0, len(last_sample))

        # Add a sample
        samples.record({})
        last_sample = samples.last()
        self.assertEqual(1, len(last_sample))
        self.assertTrue('elapsed_ms' in last_sample)

        samples.reset()
        # After reset, there should be no recorded samples again
        last_sample = samples.last()
        self.assertEqual(0, len(last_sample))

    def test_max_samples(self):
        max_samples = 3
        samples = sampler(max_samples)

        # Test empty samples
        entries = samples.samples()
        self.assertEqual(0, len(entries))

        # Test 1 sample in buffer
        samples.record({'val': 1})
        entries = samples.samples()
        self.assertEqual(1, len(entries))
        self.assertEqual(1, entries[0]['val'])

        # Test 2nd sample
        samples.record({'val': 2})
        entries = samples.samples()
        self.assertEqual(2, len(entries))
        self.assertEqual(1, entries[0]['val'])
        self.assertEqual(2, entries[1]['val'])

        # Test 3rd sample
        samples.record({'val': 3})
        entries = samples.samples()
        self.assertEqual(3, len(entries))
        self.assertEqual(1, entries[0]['val'])
        self.assertEqual(2, entries[1]['val'])
        self.assertEqual(3, entries[2]['val'])

        # Test buffer has overwritten first entry
        samples.record({'val': 4})
        entries = samples.samples()
        self.assertEqual(3, len(entries))
        self.assertEqual(2, entries[0]['val'])
        self.assertEqual(3, entries[1]['val'])
        self.assertEqual(4, entries[2]['val'])

    def test_by_key(self):
        max_samples = 3
        samples = sampler(max_samples)
        self.assertEqual([], samples.by_key('val'))
        samples.record({'val': 1})
        self.assertEqual([1], samples.by_key('val'))
        samples.record({'val': 2})
        self.assertEqual([1,2], samples.by_key('val'))
        samples.record({'val': 3})
        self.assertEqual([1,2,3], samples.by_key('val'))
        samples.record({'val': 4})
        self.assertEqual([2,3,4], samples.by_key('val'))

    def test_elapsed_ms(self):
        max_samples = 3
        samples = sampler(max_samples)
        time.sleep(1.1)
        samples.record({'val': 1})
        last_sample = samples.last()
        self.assertTrue('elapsed_ms' in last_sample)
        self.assertTrue(last_sample['elapsed_ms'] >= 1000)
        # The next assert could fail on a machine that is running under high load
        self.assertTrue(last_sample['elapsed_ms'] < 2000)

    def test_start(self):
        max_samples = 3
        samples = sampler(max_samples)
        time.sleep(1.1)
        samples.start()
        samples.record({'val': 1})
        last_sample = samples.last()
        self.assertTrue('elapsed_ms' in last_sample)
        self.assertTrue(last_sample['elapsed_ms'] < 1000)

if __name__ == "__main__":
    unittest.main()
