# A cryptographically secure hash function.
class H:
    @classmethod
    def H1(cls, cpu, name, m):
        return cpu.hash_to_scalar(name, [cls.contextString, 'rho'] + m)

    @classmethod
    def H2(cls, cpu, name, m):
        return cpu.hash_to_scalar(name, cls.H2Prefix + m)

    @classmethod
    def H3(cls, cpu, name, m):
        return cpu.hash_to_scalar(name, [cls.contextString, 'nonce'] + m)

    @classmethod
    def H4(cls, cpu, name, m):
        return cpu.hash(name, [cls.contextString, 'msg'] + m)

    @classmethod
    def H5(cls, cpu, name, m):
        return cpu.hash(name, [cls.contextString, 'com'] + m)

# An output of a cryptographic hash function.
class Digest:
    def __init__(self, mem, name, size):
        self.size = size
        self.allocation = mem.alloc_bytes(name, size)

    def name(self):
        return self.allocation.name

    def free(self):
        self.allocation.free()

    def __repr__(self):
        return 'Digest({}, {})'.format(self.name(), self.size)
