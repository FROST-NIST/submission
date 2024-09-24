from .group import Element, Scalar

class Ops:
    def __init__(self):
        self.element_muls = 0
        self.element_exps = 0
        self.element_base_exps = 0
        self.scalar_adds = 0
        self.scalar_muls = 0

    def __repr__(self):
        return '{} element muls, {} variable-base exponentiations, {} fixed-base exponentiations, {} scalar adds, {} scalar muls'.format(
            self.element_muls,
            self.element_exps,
            self.element_base_exps,
            self.scalar_adds,
            self.scalar_muls,
        )

    def __add__(self, other):
        ret = Ops()
        ret.element_muls = self.element_muls + other.element_muls
        ret.element_exps = self.element_exps + other.element_exps
        ret.element_base_exps = self.element_base_exps + other.element_base_exps
        ret.scalar_adds = self.scalar_adds + other.scalar_adds
        ret.scalar_muls = self.scalar_muls + other.scalar_muls
        return ret

    def element_mul(self):
        self.element_muls += 1

    def element_exp(self):
        self.element_exps += 1

    def element_base_exp(self):
        self.element_base_exps += 1

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
# - Tracks total computations per round (and thus overall).
class Processor:
    def __init__(self, mem):
        self.mem = mem
        self.ops = {}

    def __str__(self):
        total_ops = sum(self.ops.values(), start=Ops())
        return 'Per-round: {}\n  Total: {}'.format(self.ops, total_ops)

    def round_ops(self):
        if self.mem.round not in self.ops:
            self.ops[self.mem.round] = Ops()
        return self.ops[self.mem.round]

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
