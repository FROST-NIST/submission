# Analytical estimator of complexity.

from argparse import ArgumentParser

from .allocator import MemoryAllocator
from .group import Element, Scalar

class GroupInfo:
    def __init__(self, mem, max_participants):
        self.pk = Element(mem, 'pk')
        self.pk_i = [Element(mem, 'pk_i') for i in range(max_participants)]

    def free(self):
        self.pk.free()
        [pk_i.free() for pk_i in self.pk_i]

class Participant:
    def __init__(self, i, group_info):
        self.mem = MemoryAllocator()

        self.i = Scalar(self.mem, 'i', i)
        self.sk_i = Scalar(self.mem, 'sk_i')
        self.group_info = group_info(self.mem)

    def free(self):
        self.i.free()
        self.sk_i.free()
        self.group_info.free()

# Centralised protocol runner.
#
# - Handles communication between nodes
class Coordinator:
    def __init__(self, min_participants, num_participants, max_participants):
        assert min_participants <= num_participants
        assert num_participants <= max_participants

        self.mem = MemoryAllocator()
        self.key_holders = []

        # The Coordinator and each participant are additionally configured with common
        # group information, denoted "group info".
        def group_info(mem):
            return GroupInfo(mem, max_participants)
        self.group_info = group_info(self.mem)

        print('Creating', max_participants, 'key holders')
        for i in range(1, max_participants + 1):
            # TODO: Does coordinator need to store `i` in memory as a `Scalar`?
            self.key_holders.append(Participant(i, group_info))

        print('Selecting', num_participants, 'participants')
        self.participants = self.key_holders[:num_participants]

    def run(self):
        # Print the current memory usage.
        print('Coordinator: {}'.format(self.mem))
        for p in self.participants:
            print('Participant {}: {}'.format(p.i.value(), p.mem))

        # Finished protocol run; free the participants and group info.
        for p in self.key_holders:
            p.free()
        self.group_info.free()

def main():
    parser = ArgumentParser(
        prog='Complexity',
    )
    parser.add_argument('min_participants', type=int)
    parser.add_argument('max_participants', type=int)
    parser.add_argument('num_participants', type=int)
    args = parser.parse_args()

    coord = Coordinator(
        args.min_participants,
        args.num_participants,
        args.max_participants,
    )
    coord.run()
