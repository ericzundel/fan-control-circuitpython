"""test_sampler - some unit tests for the sampler module"""

import unittest
from sampler import sampler


class TestSampler(unittest.TestCase):

    def test_reset(self):
        """Test initialization and reset() method"""
        samples = Sampler(10)

        # There should be no recorded samples
        last_sample = samples.last()
        self.assertEqual(0, len(last_sample))

        # Add a sample
        samples.sample({})
        last_sample = samples.last()
        self.assertEqual(1, len(last_sample))
        self.assertTrue('elapsed_ms' in last_sample)

        samples.reset()
        # After reset, there should be no recorded samples again
        last_sample = samples.last()
        self.assertEqual(0, len(last_sample))


if __name__ == "__main__":
    unittest.main()
