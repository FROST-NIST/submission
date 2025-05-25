from .group import Element, Encoding, G, Scalar
from .hash import Digest, H

class Ops:
    def __init__(self):
        self.element_reads = 0
        self.element_writes = 0
        self.element_muls = 0
        self.element_exps = 0
        self.element_base_exps = 0
        self.element_multi_exps = []
        self.scalar_reads = 0
        self.scalar_writes = 0
        self.scalar_adds = 0
        self.scalar_muls = 0
        self.scalar_exps = 0
        self.hash_blocks = 0

    def __repr__(self):
        return '{} element reads, {} element writes, {} element muls, {} variable-base exponentiations, {} fixed-base exponentiations, {} variable-base multi-exponentiations with at most {} terms, {} scalar reads, {} scalar writes, {} scalar adds, {} scalar muls, {} scalar exponentiations, {} hash blocks'.format(
            self.element_reads,
            self.element_writes,
            self.element_muls,
            self.element_exps,
            self.element_base_exps,
            len(self.element_multi_exps),
            max(self.element_multi_exps),
            self.scalar_reads,
            self.scalar_writes,
            self.scalar_adds,
            self.scalar_muls,
            self.scalar_exps,
            self.hash_blocks,
        )

    def __add__(self, other):
        ret = Ops()
        ret.element_reads = self.element_reads + other.element_reads
        ret.element_writes = self.element_writes + other.element_writes
        ret.element_muls = self.element_muls + other.element_muls
        ret.element_exps = self.element_exps + other.element_exps
        ret.element_base_exps = self.element_base_exps + other.element_base_exps
        ret.element_multi_exps = self.element_multi_exps + other.element_multi_exps
        ret.scalar_reads = self.scalar_reads + other.scalar_reads
        ret.scalar_writes = self.scalar_writes + other.scalar_writes
        ret.scalar_adds = self.scalar_adds + other.scalar_adds
        ret.scalar_muls = self.scalar_muls + other.scalar_muls
        ret.scalar_exps = self.scalar_exps + other.scalar_exps
        ret.hash_blocks = self.hash_blocks + other.hash_blocks
        return ret

    def element_read(self):
        self.element_reads += 1

    def element_write(self):
        self.element_writes += 1

    def element_mul(self):
        self.element_muls += 1

    def element_exp(self):
        self.element_exps += 1

    def element_base_exp(self):
        self.element_base_exps += 1

    def element_multi_exp(self, num_terms):
        self.element_multi_exps += [num_terms]

    def scalar_read(self):
        self.scalar_reads += 1

    def scalar_write(self):
        self.scalar_writes += 1

    def scalar_add(self):
        self.scalar_adds += 1

    def scalar_sub(self):
        self.scalar_adds += 1

    def scalar_mul(self):
        self.scalar_muls += 1

    def scalar_div(self):
        # a/b (mod p) = a * b^(-1) (mod p)
        #             = a * b^(-1) * b^(p-1) (mod p) by Fermat's Little Theorem
        #             = a * b^(p-2) (mod p)
        self.scalar_muls += 1
        self.scalar_exps += 1

    def process_hash_blocks(self, n):
        self.hash_blocks += n

# Computation tracker
# - Per node
# - "Performs" computations (scalar muls, hashing, etc.)
# - Tracks total computations per round (and thus overall).
class Processor:
    def __init__(self, mem, use_multi_exponentiation):
        self.mem = mem
        self.use_multi_exponentiation = use_multi_exponentiation
        self.ops = {}

    def __str__(self):
        total_ops = sum(self.ops.values(), start=Ops())
        return 'Per-round: {}\n  Total: {}'.format(self.ops, total_ops)

    def round_ops(self):
        if self.mem.round not in self.ops:
            self.ops[self.mem.round] = Ops()
        return self.ops[self.mem.round]

    def random_bytes(self, n):
        return RandomBytes(self.mem, n)

    def element_read(self, buf):
        name = buf.name()
        if name.startswith('Serialized('):
            name = name.removeprefix('Serialized(').removesuffix(')')
        else:
            name = 'Deserialized({})'.format(name)
        self.round_ops().element_read()
        return Element(self.mem, name)

    def element_write(self, A):
        assert self.mem is A.mem, 'element on wrong machine'
        name = A.name()
        if name.startswith('Deserialized('):
            name = name.removeprefix('Deserialized(').removesuffix(')')
        else:
            name = 'Serialized({})'.format(name)
        self.round_ops().element_write()
        return Encoding(self.mem, name, G.Ne)

    def element_mul(self, P, Q):
        assert self.mem is P.mem, 'element on wrong machine'
        assert self.mem is Q.mem, 'element on wrong machine'
        self.round_ops().element_mul()
        return Element(self.mem, '({}) * ({})'.format(P.name(), Q.name()))

    def element_mul_assign(self, P, Q):
        assert self.mem is P.mem, 'element on wrong machine'
        assert self.mem is Q.mem, 'element on wrong machine'
        self.round_ops().element_mul()
        P.update('({}) * ({})'.format(P.name(), Q.name()))

    def element_exp(self, A, k):
        assert self.mem is A.mem, 'element on wrong machine'
        assert self.mem is k.mem, 'scalar on wrong machine'
        self.round_ops().element_exp()
        return Element(self.mem, '{}^{}'.format(A.name(), k.name()))

    def element_base_exp(self, k):
        assert self.mem is k.mem, 'scalar on wrong machine'
        self.round_ops().element_base_exp()
        return Element(self.mem, 'B^{}'.format(k.name()))

    def element_multi_exp(self, terms):
        assert self.use_multi_exponentiation, 'multi-exponentiation is disabled on this machine'
        for (A, k) in terms:
            assert self.mem is A.mem, 'element on wrong machine'
            assert self.mem is k.mem, 'scalar on wrong machine'
        self.round_ops().element_multi_exp(len(terms))
        return Element(
            self.mem,
            ' * '.join(['({}^{})'.format(A.name(), k.name()) for (A, k) in terms]),
        )

    def scalar_read(self, buf):
        name = buf.name()
        if name.startswith('Serialized('):
            name = name.removeprefix('Serialized(').removesuffix(')')
        else:
            name = 'Deserialized({})'.format(name)
        self.round_ops().scalar_read()
        return Scalar(self.mem, name, buf.value())

    def scalar_write(self, s):
        assert self.mem is s.mem, 'scalar on wrong machine'
        name = s.name()
        if name.startswith('Deserialized('):
            name = name.removeprefix('Deserialized(').removesuffix(')')
        else:
            name = 'Serialized({})'.format(name)
        self.round_ops().scalar_write()
        return Encoding(self.mem, name, G.Ns, s.value())

    def scalar_add(self, j, k):
        assert self.mem is j.mem, 'scalar on wrong machine'
        assert self.mem is k.mem, 'scalar on wrong machine'
        self.round_ops().scalar_add()
        if j.value() and k.value():
            res = j.value() + k.value()
        else:
            res = None
        return Scalar(
            self.mem,
            '({}) + ({})'.format(j.name(), k.name()),
            res,
        )

    def scalar_add_assign(self, j, k):
        assert self.mem is j.mem, 'scalar on wrong machine'
        assert self.mem is k.mem, 'scalar on wrong machine'
        self.round_ops().scalar_add()
        if j.value() and k.value():
            res = j.value() + k.value()
        else:
            res = None
        j.update(
            '({}) + ({})'.format(j.name(), k.name()),
            res,
        )

    def scalar_sub(self, j, k):
        assert self.mem is j.mem, 'scalar on wrong machine'
        assert self.mem is k.mem, 'scalar on wrong machine'
        self.round_ops().scalar_sub()
        if j.value() and k.value():
            res = j.value() - k.value()
        else:
            res = None
        return Scalar(
            self.mem,
            '({}) - ({})'.format(j.name(), k.name()),
            res,
        )

    def scalar_mul(self, j, k):
        assert self.mem is j.mem, 'scalar on wrong machine'
        assert self.mem is k.mem, 'scalar on wrong machine'
        self.round_ops().scalar_mul()
        if j.value() and k.value():
            res = j.value() * k.value()
        else:
            res = None
        return Scalar(
            self.mem,
            '({})*({})'.format(j.name(), k.name()),
            res,
        )

    def scalar_mul_assign(self, j, k):
        assert self.mem is j.mem, 'scalar on wrong machine'
        assert self.mem is k.mem, 'scalar on wrong machine'
        self.round_ops().scalar_mul()
        if j.value() and k.value():
            res = j.value() * k.value()
        else:
            res = None
        j.update(
            '({})*({})'.format(j.name(), k.name()),
            res,
        )

    def scalar_div(self, j, k):
        assert self.mem is j.mem, 'scalar on wrong machine'
        assert self.mem is k.mem, 'scalar on wrong machine'
        self.round_ops().scalar_div()
        if j.value() and k.value():
            res = j.value() / k.value()
        else:
            res = None
        return Scalar(
            self.mem,
            '({})/({})'.format(j.name(), k.name()),
            res,
        )

    def hash(self, name, m):
        block = self.mem.alloc_bytes('H_block', H.BlockSize)
        bytes_digested = sum([
            len(input) if type(input) == str else input.size
            for input in m
        ])
        # Ceiling division to determine how many blocks were processed.
        blocks_processed = -(bytes_digested // -H.BlockSize)
        self.round_ops().process_hash_blocks(blocks_processed)
        digest = Digest(self.mem, name, H.OutputLen)
        block.free()
        return digest

    def hash_to_scalar(self, name, m):
        # All FROST ciphersuites implement hash-to-scalar by hashing the input
        # message and then reducing the resulting digest; we assume that the
        # digest and scalar are both in memory at the same time at some point.
        digest = self.hash(name, m)
        scalar = Scalar(self.mem, name)
        digest.free()
        return scalar

# Bytes sampled from a cryptographically secure pseudorandom number generator.
class RandomBytes:
    def __init__(self, mem, size):
        self.size = size
        self.allocation = mem.alloc_bytes('random_bytes', size)

    def free(self):
        self.allocation.free()

    def __repr__(self):
        return 'RandomBytes({})'.format(self.size)
