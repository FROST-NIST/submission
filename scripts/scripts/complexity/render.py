from .communication import Traffic
from .processor import Ops

def print_complexity_tables(coordinator, participant):
    print('       Memory | Round | Elements | Scalars | Arb bytes |  Cost  |')
    print('--------------|-------|----------|---------|-----------|--------|')
    for round in [0, 1, 2]:
        round_stored = coordinator.mem.max_stored[round]
        print('  {} |   {}   |   {:4}   |   {:3}   |   {:5}   | {:6} |'.format(
            'Coordinator' if round == 0 else '           ',
            round,
            round_stored.elements,
            round_stored.scalars,
            round_stored.bytes,
            coordinator.mem.cost_model.count(round_stored),
        ))
    print('--------------|-------|----------|---------|-----------|--------|')
    for round in [0, 1, 2]:
        round_stored = participant.mem.max_stored[round]
        print('  {} |   {}   |   {:4}   |   {:3}   |   {:5}   | {:6} |'.format(
            'Participant' if round == 0 else '           ',
            round,
            round_stored.elements,
            round_stored.scalars,
            round_stored.bytes,
            participant.mem.cost_model.count(round_stored),
        ))
    print()
    print('  Computation | Round | A * A | A^k  | B^k  | k + k | k * k | H blocks |')
    print('--------------|-------|-------|------|------|-------|-------|----------|')
    for round in [0, 1, 2]:
        round_ops = coordinator.cpu.ops.get(round, Ops())
        print('  {} |   {}   | {:4}  | {:3}  | {:3}  |  {:3}  | {:4}  |   {:4}   |'.format(
            'Coordinator' if round == 0 else '           ',
            round,
            round_ops.element_muls,
            round_ops.element_exps,
            round_ops.element_base_exps,
            round_ops.scalar_adds,
            round_ops.scalar_muls,
            round_ops.hash_blocks,
        ))
    coord_total_ops = sum(coordinator.cpu.ops.values(), start=Ops())
    print('              | Total | {:4}  | {:3}  | {:3}  |  {:3}  | {:4}  |   {:4}   |'.format(
        coord_total_ops.element_muls,
        coord_total_ops.element_exps,
        coord_total_ops.element_base_exps,
        coord_total_ops.scalar_adds,
        coord_total_ops.scalar_muls,
        coord_total_ops.hash_blocks,
    ))
    print('--------------|-------|-------|------|------|-------|-------|----------|')
    for round in [0, 1, 2]:
        round_ops = participant.cpu.ops.get(round, Ops())
        print('  {} |   {}   | {:4}  | {:3}  | {:3}  |  {:3}  | {:4}  |   {:4}   |'.format(
            'Participant' if round == 0 else '           ',
            round,
            round_ops.element_muls,
            round_ops.element_exps,
            round_ops.element_base_exps,
            round_ops.scalar_adds,
            round_ops.scalar_muls,
            round_ops.hash_blocks,
        ))
    participant_total_ops = sum(participant.cpu.ops.values(), start=Ops())
    print('              | Total | {:4}  | {:3}  | {:3}  |  {:3}  | {:4}  |   {:4}   |'.format(
        participant_total_ops.element_muls,
        participant_total_ops.element_exps,
        participant_total_ops.element_base_exps,
        participant_total_ops.scalar_adds,
        participant_total_ops.scalar_muls,
        participant_total_ops.hash_blocks,
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
