# Core FROST logic.
#
# These functions implement various components of RFC 9591, and as such follow
# its notation (while annotating them with memory and computation tracking). The
# one exception is that the processor tracks computations using multiplicative
# notation to match the protocol description in the submission; this affects
# `compute_group_commitment`.

import progressbar

from .group import G, Scalar

# 4.1 Nonce generation
def nonce_generate(mem, secret, nonce_name):
    random_bytes = mem.alloc_bytes('random_bytes', 32)
    secret_enc = G.SerializeScalar(mem, secret)
    # nonce = H3(random_bytes || secret_enc)
    nonce = Scalar(mem, nonce_name)
    random_bytes.free()
    secret_enc.free()
    return nonce

# 4.2 Polynomials
def derive_interpolating_value(cpu, L, x_i):
    if x_i not in L:
        raise "invalid parameters"
    # for x_j in L:
    #     if count(x_j, L) > 1:
    #         raise "invalid parameters"

    numerator = Scalar(cpu.mem, 'numerator', 1)
    denominator = Scalar(cpu.mem, 'denominator', 1)
    for x_j in L:
        if x_j == x_i: continue
        cpu.scalar_mul_assign(numerator, x_j)
        diff = cpu.scalar_sub(x_j, x_i)
        cpu.scalar_mul_assign(denominator, diff)
        diff.free()

    value = cpu.scalar_div(numerator, denominator)
    numerator.free()
    denominator.free()
    return value

# 4.3 List Operations

def encode_group_commitment_list(mem, commitment_list):
    encoded_group_commitment_size = 0
    for (identifier, hiding_nonce_commitment, binding_nonce_commitment) in commitment_list:
        identifier_enc = G.SerializeScalar(mem, identifier)
        hiding_nonce_commitment_enc = G.SerializeElement(mem, hiding_nonce_commitment)
        binding_nonce_commitment_enc = G.SerializeElement(mem, binding_nonce_commitment)
        encoded_group_commitment_size += (
            identifier_enc.size +
            hiding_nonce_commitment_enc.size +
            binding_nonce_commitment_enc.size)
        identifier_enc.free()
        hiding_nonce_commitment_enc.free()
        binding_nonce_commitment_enc.free()
    return mem.alloc_bytes('encoded_group_commitment', encoded_group_commitment_size)

def participants_from_commitment_list(commitment_list):
    identifiers = []
    for (identifier, _, _) in commitment_list:
        identifiers.append(identifier)
    return identifiers

def binding_factor_for_participant(binding_factor_list, identifier):
    for (i, binding_factor) in binding_factor_list:
        if identifier == i:
            return binding_factor
    raise "invalid participant"

# 4.4 Binding Factors Computation
def compute_binding_factors(mem, group_public_key, commitment_list, msg):
    group_public_key_enc = G.SerializeElement(mem, group_public_key)
    # Hashed to a fixed-length.
    msg_hash = mem.alloc_bytes('H4(msg)', G.H_LEN)
    # Hashed to a fixed-length.
    encoded_group_commitment_list = encode_group_commitment_list(mem, commitment_list)
    encoded_commitment_hash = mem.alloc_bytes('H5(encoded_group_commitment_list)', G.H_LEN)
    encoded_group_commitment_list.free()

    # The encoding of the group public key is a fixed length within a ciphersuite.
    # rho_input_prefix = group_public_key_enc || msg_hash || encoded_commitment_hash
    rho_input_prefix = mem.alloc_bytes(
        'rho_input_prefix',
        group_public_key_enc.size + G.H_LEN + G.H_LEN,
    )
    group_public_key_enc.free()
    msg_hash.free()
    encoded_commitment_hash.free()

    binding_factor_list = []
    for (identifier, hiding_nonce_commitment, binding_nonce_commitment) in commitment_list:
        identifier_enc = G.SerializeScalar(mem, identifier)
        # rho_input = rho_input_prefix || identifier_enc
        binding_factor = Scalar(mem, 'H1(rho_input)')
        identifier_enc.free()
        binding_factor_list.append((identifier, binding_factor))

    rho_input_prefix.free()
    return binding_factor_list

# 4.5 Group Commitment Computation
def compute_group_commitment(cpu, commitment_list, binding_factor_list):
    group_commitment = G.Identity(cpu.mem)
    for (identifier, hiding_nonce_commitment, binding_nonce_commitment) in commitment_list:
        binding_factor = binding_factor_for_participant(binding_factor_list, identifier)
        binding_nonce = G.ScalarMult(cpu, binding_nonce_commitment, binding_factor)
        hiding_plus_binding = cpu.element_mul(hiding_nonce_commitment, binding_nonce)
        binding_nonce.free()
        cpu.element_mul_assign(group_commitment, hiding_plus_binding)
        hiding_plus_binding.free()
    return group_commitment

# 4.6 Signature Challenge Computation
def compute_challenge(mem, group_commitment, group_public_key, msg):
    group_comm_enc = G.SerializeElement(mem, group_commitment)
    group_public_key_enc = G.SerializeElement(mem, group_public_key)
    # challenge_input = group_comm_enc || group_public_key_enc || msg
    challenge = Scalar(mem, 'H2(challenge_input)')
    group_comm_enc.free()
    group_public_key_enc.free()
    return challenge

# 5.1 Round One - Commitment
def commit(cpu, sk_i):
    hiding_nonce = nonce_generate(cpu.mem, sk_i, 'hiding_nonce')
    binding_nonce = nonce_generate(cpu.mem, sk_i, 'binding_nonce')
    hiding_nonce_commitment = G.ScalarBaseMult(cpu, hiding_nonce)
    binding_nonce_commitment = G.ScalarBaseMult(cpu, binding_nonce)
    nonces = (hiding_nonce, binding_nonce)
    comms = (hiding_nonce_commitment, binding_nonce_commitment)
    return (nonces, comms)

# 5.2 Round Two - Signature Share Generation
def sign(cpu, identifier, sk_i, group_public_key, nonce_i, msg, commitment_list):
    # Compute the binding factor(s)
    binding_factor_list = compute_binding_factors(cpu.mem, group_public_key, commitment_list, msg)
    binding_factor = binding_factor_for_participant(binding_factor_list, identifier)

    # Compute the group commitment
    group_commitment = compute_group_commitment(cpu, commitment_list, binding_factor_list)

    # Compute the interpolating value
    participant_list = participants_from_commitment_list(commitment_list)
    lambda_i = derive_interpolating_value(cpu, participant_list, identifier)

    # Compute the per-message challenge
    challenge = compute_challenge(cpu.mem, group_commitment, group_public_key, msg)
    group_commitment.free()

    # Compute the signature share
    (hiding_nonce, binding_nonce) = nonce_i
    # sig_share = hiding_nonce + (binding_nonce * binding_factor) + (lambda_i * sk_i * challenge)
    nonce_part = cpu.scalar_mul(binding_nonce, binding_factor)
    cpu.scalar_add_assign(nonce_part, hiding_nonce)
    challenge_part = cpu.scalar_mul(lambda_i, sk_i)
    cpu.scalar_mul_assign(challenge_part, challenge)
    challenge.free()
    sig_share = cpu.scalar_add(nonce_part, challenge_part)
    nonce_part.free()
    challenge_part.free()
    lambda_i.free() # TODO: Model caching of this?

    # Free `binding_factor_list` here after `binding_factor` (which is a reference into
    # the list) has been used.
    for (identifier, binding_factor) in binding_factor_list:
        # Assume `binding_factor_list` contains a reference to the identifier, not the
        # full Scalar, so its memory cost is negligible.
        # TODO: Model references?
        binding_factor.free()

    return sig_share

# 5.3 Signature Share Aggregation
def aggregate(cpu, commitment_list, msg, group_public_key, sig_shares):
    # Compute the binding factors
    binding_factor_list = compute_binding_factors(cpu.mem, group_public_key, commitment_list, msg)

    # Compute the group commitment
    group_commitment = compute_group_commitment(cpu, commitment_list, binding_factor_list)
    for (identifier, binding_factor) in binding_factor_list:
        # Per above, `identifier` is a reference, don't free here.
        binding_factor.free()

    # Compute aggregated signature
    z = Scalar(cpu.mem, 'z', 0)
    for z_i in progressbar.progressbar(sig_shares):
        cpu.scalar_add_assign(z, z_i)
    return (group_commitment, z)
