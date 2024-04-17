from .group import Element, Scalar

class Ops:
    def __init__(self):
        self.element_adds = 0
        self.element_scalar_muls = 0
        self.element_scalar_base_muls = 0
        self.scalar_adds = 0
        self.scalar_muls = 0

    def __repr__(self):
        return '{} element additions, {} variable-base scalar muls, {} fixed-base scalar muls, {} scalar adds, {} scalar muls'.format(
            self.element_adds,
            self.element_scalar_muls,
            self.element_scalar_base_muls,
            self.scalar_adds,
            self.scalar_muls,
        )

    def element_add(self):
        self.element_adds += 1

    def element_scalar_mul(self):
        self.element_scalar_muls += 1

    def element_scalar_base_mul(self):
        self.element_scalar_base_muls += 1

    def scalar_add(self):
        self.scalar_adds += 1

    def scalar_sub(self):
        self.scalar_adds += 1

    def scalar_mul(self):
        self.scalar_muls += 1

    def scalar_div(self):
        # TODO: Cost model of scalar division
        self.scalar_muls += 1

# Computation tracker
# - Per node
# - "Performs" computations (scalar muls, etc.)
class Processor:
    def __init__(self, mem):
        self.mem = mem
        self.ops = Ops()

    def __str__(self):
        return 'Current: {}'.format(self.ops)

    def element_add(self, P, Q):
        assert self.mem is P.mem, 'element on wrong machine'
        assert self.mem is Q.mem, 'element on wrong machine'
        self.ops.element_add()
        return Element(self.mem, '({}) + ({})'.format(P.name(), Q.name()))

    def element_add_assign(self, P, Q):
        assert self.mem is P.mem, 'element on wrong machine'
        assert self.mem is Q.mem, 'element on wrong machine'
        self.ops.element_add()
        P.update('({}) + ({})'.format(P.name(), Q.name()))

    def element_scalar_mul(self, A, k):
        assert self.mem is A.mem, 'element on wrong machine'
        assert self.mem is k.mem, 'scalar on wrong machine'
        self.ops.element_scalar_mul()
        return Element(self.mem, '{}^{}'.format(A.name(), k.name()))

    def element_scalar_base_mul(self, k):
        assert self.mem is k.mem, 'scalar on wrong machine'
        self.ops.element_scalar_base_mul()
        return Element(self.mem, 'B^{}'.format(k.name()))

    def scalar_add(self, j, k):
        assert self.mem is j.mem, 'scalar on wrong machine'
        assert self.mem is k.mem, 'scalar on wrong machine'
        self.ops.scalar_add()
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
        self.ops.scalar_add()
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
        self.ops.scalar_sub()
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
        self.ops.scalar_mul()
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
        self.ops.scalar_mul()
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
        self.ops.scalar_div()
        if j.value() and k.value():
            res = j.value() / k.value()
        else:
            res = None
        return Scalar(
            self.mem,
            '({})/({})'.format(j.name(), k.name()),
            res,
        )
