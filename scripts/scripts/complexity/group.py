# A prime-order group `G`.
class G:
    # TODO: Make these configurable.
    Ne = 32
    Ns = 32

    @classmethod
    def Identity(cls, mem):
        return Element(mem, 'I')

    @classmethod
    def ScalarMult(cls, cpu, A, k):
        return cpu.element_scalar_mul(A, k)

    @classmethod
    def ScalarBaseMult(cls, cpu, k):
        return cpu.element_scalar_base_mul(k)

    @classmethod
    def SerializeElement(cls, mem, A):
        return Encoding(mem, 'Serialized({})'.format(A.name()), cls.Ne)

    @classmethod
    def DeserializeElement(cls, mem, buf):
        return Element(mem, 'Deserialized({})'.format(buf.name()))

    @classmethod
    def SerializeScalar(cls, mem, s):
        return Encoding(mem, 'Serialized({})'.format(s.name()), cls.Ns, s.value())

    @classmethod
    def DeserializeScalar(cls, mem, buf):
        return Scalar(mem, 'Deserialized({})'.format(buf.name()), buf.value())

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
