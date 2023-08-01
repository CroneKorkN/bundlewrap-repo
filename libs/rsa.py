# https://stackoverflow.com/a/18266970

from Crypto.PublicKey import RSA
from struct import pack
from hashlib import sha3_512
from cryptography.hazmat.primitives.serialization import load_der_private_key
from functools import cache
from cache_to_disk import cache_to_disk


class PRNG(object):
    def __init__(self, seed):
        self.index = 0
        self.seed = sha3_512(seed).digest()
        self.buffer = b""
    def __call__(self, n):
        while len(self.buffer) < n:
            self.buffer += sha3_512(self.seed + pack("<d", self.index)).digest()
            self.index += 1
        result, self.buffer = self.buffer[:n], self.buffer[n:]
        return result


@cache_to_disk(30)
def _generate_deterministic_rsa_private_key(secret_bytes, key_size):
    return RSA.generate(key_size, randfunc=PRNG(secret_bytes)).export_key('DER')

@cache
def generate_deterministic_rsa_private_key(secret_bytes, key_size=2048):
    return load_der_private_key(
        _generate_deterministic_rsa_private_key(secret_bytes, key_size),
        password=None,
    )
