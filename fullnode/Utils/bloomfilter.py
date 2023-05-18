from pybloom_live import BloomFilter
import base64
import tempfile

class BF(BloomFilter):
    def __init__(self, capacity, error_rate=0.001):
        super().__init__(capacity, error_rate)
        self.revo_map = [{} for _ in range(self.num_bits)]

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

    def add(self, key, i, j, skip_check=False):
        super().add(key, skip_check)
        hashes = self.make_hashes(key)
        offset = 0
        for k in hashes:
            self.revo_map[offset + k][key] = (i, j)
            offset += self.bits_per_slice

    def element_in_bf(self, key) -> bool:
        hashes = self.make_hashes(key)
        offset = 0
        for k in hashes:
            if key in self.revo_map[offset + k]:
                return True
            else:
                pass
            offset += self.bits_per_slice
        return False
