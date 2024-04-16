# A prime-order group `G`.
class G:
    # TODO: Make these configurable.
    Ne = 32
    Ns = 32

    @classmethod
    def Identity(cls, mem):
        return Element(mem, 'I')

    @classmethod
    def ScalarMult(cls, mem, A, k):
        # TODO: Computational cost.
        return Element(mem, '{}^{}'.format(A.name(), k.name()))

    @classmethod
    def ScalarBaseMult(cls, mem, k):
        # TODO: Computational cost.
        return Element(mem, 'B^{}'.format(k.name()))

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

    def free(self):
        self.allocation.free()

    def __add__(self, other):
        return Element(self.mem, '({}) + ({})'.format(self.name(), other.name()))

    def __iadd__(self, other):
        res = self + other
        self.free()
        return res

# An integer modulo the prime order `p` of group `G`.
class Scalar:
    def __init__(self, mem, name, value=None):
        self.mem = mem
        self.allocation = mem.alloc_scalar(name, value)

    def name(self):
        return self.allocation.name

    def value(self):
        return self.allocation.value()

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

    def __add__(self, other):
        if self.value() and other.value():
            res = self.value() + other.value()
        else:
            res = None
        return Scalar(
            self.mem,
            '({}) + ({})'.format(self.name(), other.name()),
            res,
        )

    def __iadd__(self, other):
        res = self + other
        self.free()
        return res

    def __sub__(self, other):
        if self.value() and other.value():
            res = self.value() - other.value()
        else:
            res = None
        return Scalar(
            self.mem,
            '({}) - ({})'.format(self.name(), other.name()),
            res,
        )

    def __isub__(self, other):
        res = self - other
        self.free()
        return res

    def __mul__(self, other):
        if self.value() and other.value():
            res = self.value() * other.value()
        else:
            res = None
        return Scalar(
            self.mem,
            '({})*({})'.format(self.name(), other.name()),
            res,
        )

    def __imul__(self, other):
        res = self * other
        self.free()
        return res

    def __truediv__(self, other):
        if self.value() and other.value():
            res = self.value() / other.value()
        else:
            res = None
        return Scalar(
            self.mem,
            '({})/({})'.format(self.name(), other.name()),
            res,
        )

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
