from copy import deepcopy

class CostModel:
    def __init__(self, element_bytes, scalar_bytes):
        self.element_bytes = element_bytes
        self.scalar_bytes = scalar_bytes

    def count(self, stored):
        return (
            (stored.elements * self.element_bytes) +
            (stored.scalars * self.scalar_bytes) +
            stored.bytes
        )

class Stored:
    def __init__(self):
        self.bytes = 0
        self.elements = 0
        self.scalars = 0

    def __repr__(self):
        return '{} bytes, {} elements, {} scalars'.format(
            self.bytes,
            self.elements,
            self.scalars,
        )

    def is_greater_than(self, other, cost_model):
        return cost_model.count(self) > cost_model.count(other)

    def alloc_bytes(self, size):
        self.bytes += size

    def free_bytes(self, size):
        self.bytes -= size

    def alloc_element(self):
        self.elements += 1

    def free_element(self):
        self.elements -= 1

    def alloc_scalar(self):
        self.scalars += 1

    def free_scalar(self):
        self.scalars -= 1

# Memory tracker.
#
# - Per node
# - Allocates and frees points, scalars, etc.
# - Tracks high water mark and what the allocation was that caused it.
#   - Per round (and thus overall).
class MemoryAllocator:
    def __init__(self, cost_model):
        self.cost_model = cost_model
        self.round = 0
        self.stored = Stored()
        self.max_stored = {}

    def __str__(self):
        return 'Current: {}\n  Max: {}'.format(self.stored, self.max_stored)

    def set_round(self, round):
        self.round = round

    def update_max_stored(self, name):
        if self.round in self.max_stored:
            if self.stored.is_greater_than(self.max_stored[self.round][0], self.cost_model):
                self.max_stored[self.round] = (deepcopy(self.stored), name)
        else:
            self.max_stored[self.round] = (deepcopy(self.stored), name)

    def alloc_bytes(self, name, size, value=None):
        self.stored.alloc_bytes(size)
        self.update_max_stored(name)
        return Allocation(lambda: self.free_bytes(size), name, value)

    def free_bytes(self, size):
        self.stored.free_bytes(size)

    def alloc_element(self, name):
        self.stored.alloc_element()
        self.update_max_stored(name)
        return Allocation(self.free_element, name, None)

    def free_element(self):
        self.stored.free_element()

    def alloc_scalar(self, name, value=None):
        self.stored.alloc_scalar()
        self.update_max_stored(name)
        return Allocation(self.free_scalar, name, value)

    def free_scalar(self):
        self.stored.free_scalar()

# An allocation in memory.
#
# Allocations should be explicitly freed to correctly model memory usage across protocol
# rounds. Allocations complain loudly if they are implicitly freed.
class Allocation:
    def __init__(self, dealloc, name, value):
        self.dealloc = dealloc
        self.name = name
        self._value = value
        self.live = True

    def __del__(self):
        if self.live:
            print('Freeing', self.name, 'that was not explicitly freed')
            self.free()

    def value(self):
        assert self.live, 'Use-after-free of ' + self.name
        return self._value

    def update(self, name, value=None):
        assert self.live, 'Use-after-free of ' + self.name
        self.name = name
        self._value = value

    def free(self):
        assert self.live, 'Double-free of ' + self.name
        self.dealloc()
        self.live = False
