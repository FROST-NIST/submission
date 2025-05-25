# Analytical estimator of complexity.

from argparse import ArgumentParser, BooleanOptionalAction
import progressbar

from . import frost
from .allocator import MemoryAllocator
from .communication import Traffic
from .group import G, Element, Scalar, Encoding
from .hash import H
from .processor import Processor
from .render import ComplexityTables, print_complexity_tables

class GroupInfo:
    def __init__(self, mem, max_participants):
        self.pk = Element(mem, 'pk')
        self.pk_i = [Element(mem, 'pk_i') for i in range(max_participants)]

    def free(self):
        self.pk.free()
        [pk_i.free() for pk_i in self.pk_i]

class Participant:
    def __init__(self, i, group_info, mem_cost_model, use_multi_exponentiation):
        self.mem = MemoryAllocator(mem_cost_model)
        self.cpu = Processor(self.mem, use_multi_exponentiation)
        self.traffic = {}

        self.i = Scalar(self.mem, 'i', i)
        self.sk_i = Scalar(self.mem, 'sk_i')
        self.group_info = group_info(self.mem)

    def free(self):
        self.i.free()
        self.sk_i.free()
        self.group_info.free()

    def round_traffic(self):
        if self.mem.round not in self.traffic:
            self.traffic[self.mem.round] = Traffic()
        return self.traffic[self.mem.round]

    def round_1(self):
        (nonces, comms) = frost.commit(self.cpu, self.sk_i)

        # The outputs `nonce` and `comm` from participant `P_i` are both stored locally
        # and kept for use in the second round.
        self.nonces = nonces
        self.comms = comms

        # [T]he public output `comm` is sent to the Coordinator.
        return (G.SerializeElement(self.cpu, self.comms[0]), G.SerializeElement(self.cpu, self.comms[1]))

    def round_2(self, msg, commitment_list_enc):
        # Each participant MUST validate the inputs before processing the Coordinator's
        # request. In particular, the signer MUST validate commitment_list, deserializing
        # each group Element in the list using DeserializeElement.
        commitment_list = []
        for (i, hiding_nonce_commitment_i, binding_nonce_commitment_i) in commitment_list_enc:
            commitment_list.append((
                G.DeserializeScalar(self.cpu, i),
                G.DeserializeElement(self.cpu, hiding_nonce_commitment_i),
                G.DeserializeElement(self.cpu, binding_nonce_commitment_i),
            ))
            i.free()
            hiding_nonce_commitment_i.free()
            binding_nonce_commitment_i.free()

        # Moreover, each participant MUST ensure that its identifier and commitments (from
        # the first round) appear in commitment_list.
        (hiding_nonce_commitment, binding_nonce_commitment) = self.comms
        assert (self.i, hiding_nonce_commitment, binding_nonce_commitment) in commitment_list
        hiding_nonce_commitment.free()
        binding_nonce_commitment.free()
        self.comms = None

        # Applications that restrict participants from processing arbitrary input messages
        # are also required to perform relevant application-layer input validation checks.
        # We do not model these here.

        # Upon receipt and successful input validation, each Signer then runs the
        # following procedure to produce its own signature share.
        sig_share = frost.sign(
            self.cpu,
            self.i,
            self.sk_i,
            self.group_info.pk,
            self.nonces,
            msg,
            commitment_list,
        )
        for (i, hiding_nonce_commitment_i, binding_nonce_commitment_i) in commitment_list:
            i.free()
            hiding_nonce_commitment_i.free()
            binding_nonce_commitment_i.free()

        # Each participant then sends these shares back to the Coordinator.
        sig_share_enc = G.SerializeScalar(self.cpu, sig_share)
        sig_share.free()

        # Each participant MUST delete the nonce and corresponding commitment after
        # completing sign, and MUST NOT use the nonce as input more than once to sign.
        (hiding_nonce, binding_nonce) = self.nonces
        hiding_nonce.free()
        binding_nonce.free()
        self.nonces = None
        # We deleted the commitment after confirming it appeared in commitment_list.

        return sig_share_enc

# Centralised protocol runner.
#
# - Handles communication between nodes
class Coordinator:
    def __init__(
        self,
        min_participants,
        num_participants,
        max_participants,
        mem_cost_model,
        use_multi_exponentiation,
    ):
        assert min_participants <= num_participants
        assert num_participants <= max_participants

        self.mem = MemoryAllocator(mem_cost_model)
        self.cpu = Processor(self.mem, use_multi_exponentiation)
        self.key_holders = []

        # The Coordinator and each participant are additionally configured with common
        # group information, denoted "group info".
        def group_info(mem):
            return GroupInfo(mem, max_participants)
        self.group_info = group_info(self.mem)

        print('Creating', max_participants, 'key holders')
        for i in progressbar.progressbar(range(1, max_participants + 1)):
            self.key_holders.append(Participant(
                i,
                group_info,
                mem_cost_model,
                use_multi_exponentiation,
            ))

        print('Selecting', num_participants, 'participants')
        # These are Python references to the individual participants for the simulator to
        # use, not anything stored in the Coordinator's memory.
        self.participants = self.key_holders[:num_participants]
        # These are what the Coordinator actually stores when managing the protocol.
        # - We store participant indices as in-memory scalars to match what is implied by
        #   the protocol description in RFC 9591, despite it being possible to store
        #   `G.SerializeScalar(i)` instead (as the scalar is never used for arithmetic by
        #   the Coordinator). The difference is negligible for cost models where scalars
        #   are stored as packed limbs in memory, but could be meaningful in other cost
        #   models.
        self.participant_indices = {
            p: Scalar(self.mem, 'i', p.i.value())
            for p in self.participants
        }

    def set_round(self, round):
        self.mem.set_round(round)
        for p in self.participants:
            p.mem.set_round(round)

    def send_encoding(self, p, buf, transient=False):
        p.round_traffic().receive(buf.size)
        ret = Encoding(p.mem, buf.name(), buf.size, buf.value())
        if transient:
            buf.free()
        return ret

    def receive_encoding(self, p, buf):
        p.round_traffic().send(buf.size)
        ret = Encoding(self.mem, buf.name(), buf.size, buf.value())
        buf.free()
        return ret

    def run(self, tables):
        print('Running round 1')
        self.set_round(1)
        commitment_list_enc = []
        for p in progressbar.progressbar(self.participants):
            (hiding_nonce_commitment_i, binding_nonce_commitment_i) = p.round_1()
            commitment_list_enc.append((
                # `i` is a reference here, don't allocate it.
                self.participant_indices[p],
                self.receive_encoding(p, hiding_nonce_commitment_i),
                self.receive_encoding(p, binding_nonce_commitment_i),
            ))

        print('Running round 2')
        self.set_round(2)
        msg = '' # TODO Model memory usage?
        sig_shares = []
        for p in progressbar.progressbar(self.participants):
            commitment_list_i = [(
                self.send_encoding(p, G.SerializeScalar(self.cpu, i), True),
                self.send_encoding(p, hiding_nonce_commitment_i),
                self.send_encoding(p, binding_nonce_commitment_i),
            ) for (i, hiding_nonce_commitment_i, binding_nonce_commitment_i) in commitment_list_enc]
            sig_share_i = self.receive_encoding(p, p.round_2(msg, commitment_list_i))
            # Before aggregating, the Coordinator MUST validate each signature share using
            # `DeserializeScalar`.
            sig_shares.append(G.DeserializeScalar(self.cpu, sig_share_i))
            sig_share_i.free()

        print('Aggregating signature')
        # The spec does not require the Coordinator to validate the commitments received
        # from participants before broadcasting them in round 2, so we don't bother
        # deserializing them until they are needed here.
        commitment_list = []
        for (i, hiding_nonce_commitment_i, binding_nonce_commitment_i) in commitment_list_enc:
            commitment_list.append((
                i,
                G.DeserializeElement(self.cpu, hiding_nonce_commitment_i),
                G.DeserializeElement(self.cpu, binding_nonce_commitment_i),
            ))
            # `i` is a reference here, don't free it.
            hiding_nonce_commitment_i.free()
            binding_nonce_commitment_i.free()
        sig = frost.aggregate(self.cpu, commitment_list, msg, self.group_info.pk, sig_shares)

        # Assume successful aggregation; free the inputs.
        for (i, hiding_nonce_commitment_i, binding_nonce_commitment_i) in commitment_list:
            # `i` is a reference here, don't free it.
            hiding_nonce_commitment_i.free()
            binding_nonce_commitment_i.free()
        for sig_share_i in sig_shares:
            sig_share_i.free()

        # Print the complexities.
        print()
        print_complexity_tables(self, self.participants[0])
        tables.update(self, self.participants[0])

        # Finished protocol run; free the signature, participants, and group info.
        sig[0].free()
        sig[1].free()
        for i in self.participant_indices.values():
            i.free()
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
    parser.add_argument('security_strength', type=int, choices=[128, 224])
    parser.add_argument('--multiexp', action=BooleanOptionalAction)
    args = parser.parse_args()

    # Current assumptions:
    # - Elements are curve points stored in projective (X, Y, T) coordinates.
    # - Scalars are stored as packed limbs in memory; any unpacking or repacking cost is
    #   bundled into the cost of scalar operations (as opposed to e.g. storing scalars in
    #   Montgomery form which would instead incur a cost during (de)serialization).
    if args.security_strength == 128:
        # FROST(Ed25519, SHA-512)
        G.Ne = 32
        G.Ns = 32
        H.OutputLen = 64
        H.contextString = 'FROST-ED25519-SHA512-v1'
        H.BlockSize = 128
        H.H2Prefix = []
        mem_cost_model = allocator.CostModel(G.Ne * 3, G.Ns)
    elif args.security_strength == 224:
        # FROST(Ed448, SHAKE256)
        G.Ne = 57
        G.Ns = 57
        H.OutputLen = 114
        H.contextString = 'FROST-ED448-SHAKE256-v1'
        H.BlockSize = 136
        H.H2Prefix = ['SigEd448', '\0', '\0']
        mem_cost_model = allocator.CostModel(G.Ne * 3, G.Ns)
    else:
        assert False

    coord = Coordinator(
        args.min_participants,
        args.num_participants,
        args.max_participants,
        mem_cost_model,
        args.multiexp,
    )
    coord.run(ComplexityTables(args))
