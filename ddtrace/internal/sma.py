from __future__ import division


class SimpleMovingAverage(object):
    """
    Simple Moving Average implementation.
    """

    __slots__ = (
        "sum",
        "index",
        "size",
        "buckets",
    )

    def __init__(self, size):
        """
        Constructor for SimpleMovingAverage.

        :param size: The size of the window to calculate the moving average.
        :type size: :obj:`int`
        """
        self.sum = 0.0
        self.index = 0
        self.size = max(1, size)
        self.buckets = [0.0] * self.size

    def get(self):
        """
        Get the current SMA value.
        """
        return self.sum / self.size

    def set(self, value):
        """
        Set the value of the next bucket and update the SMA value.

        :param value: The value of the next bucket.
        :type size: :obj:`float`
        """
        new_sum = self.sum
        new_sum -= self.buckets[self.index]
        new_sum += value

        self.buckets[self.index] = value
        self.index = (self.index + 1) % self.size

        self.sum = new_sum
