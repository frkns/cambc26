import inspect


syms = ('symV', 1), ('symH', 1), ('symR', 1)


COMMS_SCHEMAS = [
    # symmetry bits and position of some random titanium ores
    ('simple1', [*syms, ('tix', 6), ('tiy', 6)]),
]

# ==================================

# auto-size type header
TYPE_BITS = max(1, (len(COMMS_SCHEMAS) - 1).bit_length())

comms_entries = []

for type_id, (name, fields) in enumerate(COMMS_SCHEMAS):
    assert TYPE_BITS + \
        sum(b for _, b in fields) <= 32, f"{name} overflows 32 bits"

    shift = 32 - TYPE_BITS
    pack_parts = [f'({type_id} << {shift})']
    unpack_parts = []
    field_names = []

    for fname, bits in fields:
        shift -= bits
        mask = (1 << bits) - 1
        pack_parts.append(f'(({fname} & {mask}) << {shift})')
        unpack_parts.append(f'((val >> {shift}) & {mask})')
        field_names.append(fname)

    comms_entries.append({
        'name': name,
        'NAME': name.upper(),
        'type_id': type_id,
        'sig': ', '.join(field_names),
        'pack_expr': ' | '.join(pack_parts),
        'unpack_tuple': ', '.join(unpack_parts),
    })


def register(env):
    env.globals.update({
        'TYPE_BITS': TYPE_BITS,
        'COMMS_SCHEMAS': COMMS_SCHEMAS,
        'comms_entries': comms_entries,
    })
