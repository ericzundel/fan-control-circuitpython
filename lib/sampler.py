"""Library to store a circular buffer of up to a max number of samples in CircuitPython

Each time record() is called, the dictionary passed is logged along with
the following keys:

elapsed_ms: records the number of milliseconds elapsed since the last call
to either record() or start()
"""

import time


class sampler:
    def __init__(self, max_samples):
        """Initializes the sampler

        Args:
        max_samples: max number of samples to save

        Returns:
        None.
        """

        self._max_samples = max_samples

        # Put all initialization into reset() so callers can restart
        # the sampler.
        self.reset()

    def reset(self):
        """Reset all the data in the module (other than max_samples)

        Returns:
        None.
        """
        self._samples = [{} for i in range(self._max_samples)]
        self._last = 0  # indexes the position of the last used slot in _samples
        self._next = 0  # indexes the position of the next slot to use in _samples
        self.start()

    def start(self):
        """Start the timer for the next sample"""
        self._last_record_time_ns = time.monotonic_ms()

    def record(self, sample_data):
        """Record a dictionary in the data

        Args:
        sample_data: a dictionary with values to save.

        Returns:
        None
        """
        sample = sample_data.copy()
        sample["elapsed_ms"] = (
            time.monotonic_ms() - self._last_record_time_ns
        ) / 1000000
        self._samples[self._next] = sample

        # Update the indexes into our circular buffer
        self._last = self._next
        self._next = (self._next + 1) % self._max_samples

        # Restart the timer
        self.start()

    def last(self):
        """Retrieve the last sample.

        Returns:
        A copy of the dictionary stored by the last call to record().
        """
        return self._samples[self._last].copy()

    def by_key(self, key, filler=None):
        """Retrieve all data by key.

        Returns: an array of all values that match the specified key in the
        recorded samples.

        If 'filler' is None, the method will skip samples that do not contain the key.
        Otherwise, the array will be filled with the value in 'filler'
        """
        result = []
        for sample in self._samples:
            if key in sample:
                result.add(sample["key"])
            elif filler:
                result.add(filler)
        return result
