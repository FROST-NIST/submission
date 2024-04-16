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
class MemoryAllocator:
    def __init__(self):
        self.stored = Stored()

    def __str__(self):
        return 'Current: {}'.format(self.stored)

    def alloc_bytes(self, name, size, value=None):
        self.stored.alloc_bytes(size)
        return Allocation(lambda: self.free_bytes(size), name, value)

    def free_bytes(self, size):
        self.stored.free_bytes(size)

    def alloc_element(self, name):
        self.stored.alloc_element()
        return Allocation(self.free_element, name, None)

    def free_element(self):
        self.stored.free_element()

    def alloc_scalar(self, name, value=None):
        self.stored.alloc_scalar()
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

    def free(self):
        assert self.live, 'Double-free of ' + self.name
        self.dealloc()
        self.live = False
