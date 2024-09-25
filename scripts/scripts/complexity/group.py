# A prime-order group `G`.
#
# This class provides the group object specified in RFC 9591 Section 3.1, which
# uses additive notation. The processor tracks computations using multiplicative
# notation to match the protocol description in the submission. We map between
# the two notations inside the relevant member functions.
class G:
    @classmethod
    def Identity(cls, mem):
        return Element(mem, 'I')

    @classmethod
    def ScalarMult(cls, cpu, A, k):
        return cpu.element_exp(A, k)

    @classmethod
    def ScalarBaseMult(cls, cpu, k):
        return cpu.element_base_exp(k)

    @classmethod
    def MultiScalarMult(cls, cpu, terms):
        return cpu.element_multi_exp(terms)

    @classmethod
    def SerializeElement(cls, mem, A):
        name = A.name()
        if name.startswith('Deserialized('):
            name = name.removeprefix('Deserialized(').removesuffix(')')
        else:
            name = 'Serialized({})'.format(name)
        return Encoding(mem, name, cls.Ne)

    @classmethod
    def DeserializeElement(cls, mem, buf):
        name = buf.name()
        if name.startswith('Serialized('):
            name = name.removeprefix('Serialized(').removesuffix(')')
        else:
            name = 'Deserialized({})'.format(name)
        return Element(mem, name)

    @classmethod
    def SerializeScalar(cls, mem, s):
        name = s.name()
        if name.startswith('Deserialized('):
            name = name.removeprefix('Deserialized(').removesuffix(')')
        else:
            name = 'Serialized({})'.format(name)
        return Encoding(mem, name, cls.Ns, s.value())

    @classmethod
    def DeserializeScalar(cls, mem, buf):
        name = buf.name()
        if name.startswith('Serialized('):
            name = name.removeprefix('Serialized(').removesuffix(')')
        else:
            name = 'Deserialized({})'.format(name)
        return Scalar(mem, name, buf.value())

# An element of a prime-order group `G`.
class Element:
    def __init__(self, mem, name):
        self.mem = mem
        self.allocation = mem.alloc_element(name)

    def name(self):
        return self.allocation.name

    def update(self, name):
        self.allocation.update(name)

    def free(self):
        self.allocation.free()

# An integer modulo the prime order `p` of group `G`.
class Scalar:
    def __init__(self, mem, name, value=None):
        self.mem = mem
        self.allocation = mem.alloc_scalar(name, value)

    def name(self):
        return self.allocation.name

    def value(self):
        return self.allocation.value()

    def update(self, name, value=None):
        self.allocation.update(name, value)

    def free(self):
        self.allocation.free()

    def __repr__(self):
        if self.value():
            return 'Scalar({}; {})'.format(self.name(), self.value())
        else:
            return 'Scalar({})'.format(self.name())

    def __eq__(self, other):
        # Only define equality for scalars with known values (namely identifiers).
        return self.value() and other.value() and self.value() == other.value()

# A byte encoding of an element or scalar.
class Encoding:
    def __init__(self, mem, name, size, value=None):
        # Unlike Element and Scalar, we don't save `mem` here for use in derived
        # allocations, because those may be on a different machine.
        self.size = size
        self.allocation = mem.alloc_bytes(name, size, value)

    def name(self):
        return self.allocation.name

    def value(self):
        return self.allocation.value()

    def free(self):
        self.allocation.free()

    def __repr__(self):
        if self.value():
            return 'Encoding({}, {}; {})'.format(self.name(), self.size, self.value())
        else:
            return 'Encoding({}, {})'.format(self.name(), self.size)
