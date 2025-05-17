from .communication import Traffic
from .processor import Ops

def print_complexity_tables(coordinator, participant):
    print('       Memory | Round | Elements | Scalars | Arb bytes |  Cost  | Allocation causing max')
    print('--------------|-------|----------|---------|-----------|--------|-----------------------')
    for round in [0, 1, 2]:
        (round_stored, name) = coordinator.mem.max_stored[round]
        print('  {} |   {}   |   {:4}   |   {:3}   |   {:5}   | {:6} | {}'.format(
            'Coordinator' if round == 0 else '           ',
            round,
            round_stored.elements,
            round_stored.scalars,
            round_stored.bytes,
            coordinator.mem.cost_model.count(round_stored),
            name,
        ))
    print('--------------|-------|----------|---------|-----------|--------|-----------------------')
    for round in [0, 1, 2]:
        (round_stored, name) = participant.mem.max_stored[round]
        print('  {} |   {}   |   {:4}   |   {:3}   |   {:5}   | {:6} | {}'.format(
            'Participant' if round == 0 else '           ',
            round,
            round_stored.elements,
            round_stored.scalars,
            round_stored.bytes,
            participant.mem.cost_model.count(round_stored),
            name,
        ))
    print()
    used_multiexp = coordinator.cpu.use_multi_exponentiation or participant.cpu.use_multi_exponentiation
    print('  Computation | Round | A * A | A^k  | B^k  | k + k | k * k | k^n | H blocks |{}'.format(
        ' Multiexp lengths' if used_multiexp else '',
    ))
    print('--------------|-------|-------|------|------|-------|-------|-----|----------|{}'.format(
        '-----------------' if used_multiexp else '',
    ))
    for round in [0, 1, 2]:
        round_ops = coordinator.cpu.ops.get(round, Ops())
        print('  {} |   {}   | {:4}  | {:3}  | {:3}  |  {:3}  | {:4}  |  {}  |   {:4}   |{}'.format(
            'Coordinator' if round == 0 else '           ',
            round,
            round_ops.element_muls,
            round_ops.element_exps,
            round_ops.element_base_exps,
            round_ops.scalar_adds,
            round_ops.scalar_muls,
            round_ops.scalar_exps,
            round_ops.hash_blocks,
            ' {}'.format(round_ops.element_multi_exps) if coordinator.cpu.use_multi_exponentiation else '',
        ))
    coord_total_ops = sum(coordinator.cpu.ops.values(), start=Ops())
    print('              | Total | {:4}  | {:3}  | {:3}  |  {:3}  | {:4}  |  {}  |   {:4}   |{}'.format(
        coord_total_ops.element_muls,
        coord_total_ops.element_exps,
        coord_total_ops.element_base_exps,
        coord_total_ops.scalar_adds,
        coord_total_ops.scalar_muls,
        coord_total_ops.scalar_exps,
        coord_total_ops.hash_blocks,
        ' {}'.format(coord_total_ops.element_multi_exps) if coordinator.cpu.use_multi_exponentiation else '',
    ))
    print('--------------|-------|-------|------|------|-------|-------|-----|----------|{}'.format(
        '-----------------' if used_multiexp else '',
    ))
    for round in [0, 1, 2]:
        round_ops = participant.cpu.ops.get(round, Ops())
        print('  {} |   {}   | {:4}  | {:3}  | {:3}  |  {:3}  | {:4}  |  {}  |   {:4}   |{}'.format(
            'Participant' if round == 0 else '           ',
            round,
            round_ops.element_muls,
            round_ops.element_exps,
            round_ops.element_base_exps,
            round_ops.scalar_adds,
            round_ops.scalar_muls,
            round_ops.scalar_exps,
            round_ops.hash_blocks,
            ' {}'.format(round_ops.element_multi_exps) if participant.cpu.use_multi_exponentiation else '',
        ))
    participant_total_ops = sum(participant.cpu.ops.values(), start=Ops())
    print('              | Total | {:4}  | {:3}  | {:3}  |  {:3}  | {:4}  |  {}  |   {:4}   |{}'.format(
        participant_total_ops.element_muls,
        participant_total_ops.element_exps,
        participant_total_ops.element_base_exps,
        participant_total_ops.scalar_adds,
        participant_total_ops.scalar_muls,
        participant_total_ops.scalar_exps,
        participant_total_ops.hash_blocks,
        ' {}'.format(participant_total_ops.element_multi_exps) if participant.cpu.use_multi_exponentiation else '',
    ))
    print()
    print('Communication | Round | Download |  Upload  |')
    print('--------------|-------|----------|----------|')
    for round in [0, 1, 2]:
        round_traffic = sum([p.traffic.get(round, Traffic()) for p in coordinator.participants], start=Traffic())
        print('  {} |   {}   |  {:5}   | {:8} |'.format(
            'Coordinator' if round == 0 else '           ',
            round,
            round_traffic.upload,
            round_traffic.download,
        ))
    coord_total_traffic = sum([sum(p.traffic.values(), start=Traffic()) for p in coordinator.participants], start=Traffic())
    print('              | Total |  {:5}   | {:8} |'.format(
        coord_total_traffic.upload,
        coord_total_traffic.download,
    ))
    print('--------------|-------|----------|----------|')
    for round in [0, 1, 2]:
        round_traffic = participant.traffic.get(round, Traffic())
        print('  {} |   {}   |  {:5}   | {:8} |'.format(
            'Participant' if round == 0 else '           ',
            round,
            round_traffic.download,
            round_traffic.upload,
        ))
    participant_total_traffic = sum(participant.traffic.values(), start=Traffic())
    print('              | Total |  {:5}   | {:8} |'.format(
        participant_total_traffic.download,
        participant_total_traffic.upload,
    ))

def latex_memory_complexity_table(coordinator, participant):
    s = '''	\\begin{tabular}{c c c c c c}
		\\toprule
		Memory & Round & Elements & Scalars & Arb bytes & Cost \\\\ \\midrule
'''
    for round in [0, 1, 2]:
        (round_stored, name) = coordinator.mem.max_stored[round]
        s += '		{} & {} & {} & {} & {} & {} \\\\\n'.format(
            'Coordinator' if round == 0 else '           ',
            round,
            round_stored.elements,
            round_stored.scalars,
            round_stored.bytes,
            coordinator.mem.cost_model.count(round_stored),
        )
    s += '		\\midrule\n'
    for round in [0, 1, 2]:
        (round_stored, name) = participant.mem.max_stored[round]
        s += '		{} & {} & {} & {} & {} & {} \\\\\n'.format(
            'Participant' if round == 0 else '           ',
            round,
            round_stored.elements,
            round_stored.scalars,
            round_stored.bytes,
            participant.mem.cost_model.count(round_stored),
        )
    return s + '		\\bottomrule\n	\\end{tabular}\n'

def latex_computational_complexity_table(coordinator, participant):
    s = '''	\\begin{tabular}{c c c c c c c c c}
		\\toprule
		Computation & Round & $A \\times A$ & $A^k$  & $B^k$  & $k + k$ & $k \\times k$ & $k^n$ & H blocks \\\\ \\midrule
'''
    # There is no computation in "round 0".
    for round in [1, 2]:
        round_ops = coordinator.cpu.ops.get(round, Ops())
        s += '		{} & {} & {} & {} & {} & {} & {} & {} & {} \\\\\n'.format(
            'Coordinator' if round == 1 else '           ',
            round,
            round_ops.element_muls,
            round_ops.element_exps,
            round_ops.element_base_exps,
            round_ops.scalar_adds,
            round_ops.scalar_muls,
            round_ops.scalar_exps,
            round_ops.hash_blocks,
        )
    coord_total_ops = sum(coordinator.cpu.ops.values(), start=Ops())
    s += '		            & Total & {} & {} & {} & {} & {} & {} & {} \\\\\n'.format(
        coord_total_ops.element_muls,
        coord_total_ops.element_exps,
        coord_total_ops.element_base_exps,
        coord_total_ops.scalar_adds,
        coord_total_ops.scalar_muls,
        coord_total_ops.scalar_exps,
        coord_total_ops.hash_blocks,
    )
    s += '		\\midrule\n'
    for round in [1, 2]:
        round_ops = participant.cpu.ops.get(round, Ops())
        s += '		{} & {} & {} & {} & {} & {} & {} & {} & {} \\\\\n'.format(
            'Participant' if round == 1 else '           ',
            round,
            round_ops.element_muls,
            round_ops.element_exps,
            round_ops.element_base_exps,
            round_ops.scalar_adds,
            round_ops.scalar_muls,
            round_ops.scalar_exps,
            round_ops.hash_blocks,
        )
    participant_total_ops = sum(participant.cpu.ops.values(), start=Ops())
    s += '		            & Total & {} & {} & {} & {} & {} & {} & {} \\\\\n'.format(
        participant_total_ops.element_muls,
        participant_total_ops.element_exps,
        participant_total_ops.element_base_exps,
        participant_total_ops.scalar_adds,
        participant_total_ops.scalar_muls,
        participant_total_ops.scalar_exps,
        participant_total_ops.hash_blocks,
    )
    return s + '		\\bottomrule\n	\\end{tabular}\n'

def latex_communication_complexity_table(coordinator, participant):
    s = '''	\\begin{tabular}{c c c c}
		\\toprule
		Communication & Round & Download & Upload \\\\ \\midrule
'''
    # There is no communication in "round 0".
    for round in [1, 2]:
        round_traffic = sum([p.traffic.get(round, Traffic()) for p in coordinator.participants], start=Traffic())
        s += '		{} & {} & {} & {} \\\\\n'.format(
            'Coordinator' if round == 1 else '           ',
            round,
            round_traffic.upload,
            round_traffic.download,
        )
    coord_total_traffic = sum([sum(p.traffic.values(), start=Traffic()) for p in coordinator.participants], start=Traffic())
    s += '		            & Total & {} & {} \\\\\n'.format(
        coord_total_traffic.upload,
        coord_total_traffic.download,
    )
    s += '		\\midrule\n'
    for round in [1, 2]:
        round_traffic = participant.traffic.get(round, Traffic())
        s += '		{} & {} & {} & {} \\\\\n'.format(
            'Participant' if round == 1 else '           ',
            round,
            round_traffic.download,
            round_traffic.upload,
        )
    participant_total_traffic = sum(participant.traffic.values(), start=Traffic())
    s += '		            & Total & {} & {} \\\\\n'.format(
        participant_total_traffic.download,
        participant_total_traffic.upload,
    )
    return s + '		\\bottomrule\n	\\end{tabular}\n'

def replace_at_marker(contents, marker, replacement):
    begin_marker = '% BEGIN {}\n'.format(marker)
    end_marker = '% END {}\n'.format(marker)

    start = contents.find(begin_marker)
    if start < 0:
        print('Warning: missing table marker ' + marker)
        return contents
    else:
        start += len(begin_marker)

        end = contents.rfind(end_marker)
        assert end >= start

        return contents[:start] + replacement + contents[end:]

class ComplexityTables:
    def __init__(self, args):
        self.min_participants = args.min_participants
        self.num_participants = args.num_participants
        self.max_participants = args.max_participants
        self.security_strength = args.security_strength

    def marker(self, kind):
        return '{}-{}-{}-{}-{}'.format(
            kind,
            self.min_participants,
            self.max_participants,
            self.num_participants,
            self.security_strength,
        )

    def update(self, coordinator, participant):
        COMPLEXITY_TEX = '../m1/sections/complexity.tex'

        print('Updating LaTeX tables...')

        with open(COMPLEXITY_TEX, 'r') as f:
            contents = f.read()

        contents = replace_at_marker(
            contents,
            self.marker('memory'),
            latex_memory_complexity_table(coordinator, participant),
        )

        contents = replace_at_marker(
            contents,
            self.marker('computational'),
            latex_computational_complexity_table(coordinator, participant),
        )

        contents = replace_at_marker(
            contents,
            self.marker('communication'),
            latex_communication_complexity_table(coordinator, participant),
        )

        with open(COMPLEXITY_TEX, 'w') as f:
            f.write(contents)

        print('Done!')
