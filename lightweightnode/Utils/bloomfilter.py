from pybloom_live import BloomFilter
import base64
import tempfile

class BF(BloomFilter):
    def __init__(self, capacity, error_rate=0.001):
        super().__init__(capacity, error_rate)

    def tobase64(self):
        with tempfile.TemporaryFile() as tf:
            self.tofile(tf)
            tf.seek(0)
            return base64.b64encode(tf.read()).decode()

    @classmethod
    def frombase64(cls, base64_str):
        with tempfile.TemporaryFile() as tf:
            tf.write(base64.b64decode(base64_str.encode()))
            tf.seek(0)
            return cls.fromfile(tf)
