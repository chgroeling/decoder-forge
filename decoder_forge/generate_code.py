import logging
import shutil
import subprocess
import yaml

from decoder_forge.bit_pattern import BitPattern
from decoder_forge.pattern_algorithms import (
    assign_uids,
    build_decode_tree_by_fixed_bits,
    flatten_decode_tree,
)
from math import ceil

from arm_transpiller import (
    ArmType,
    PythonGenerator,
    bits,
    extract_conditionally_assigned,
    extract_input_variables,
    extract_output_variables,
    extract_side_effects,
    extract_subsumed_variables,
    extract_unassigned_inputs,
    get_runtime_source,
    infer_types,
    parse,
)
from arm_transpiller.known_types import join_types

logger = logging.getLogger(__name__)


def _format_code(code: str) -> str:
    """Auto-format the generated code with ruff.

    Runs ``ruff format`` on the generated source; falls back to the unformatted code if
    ruff is not on ``PATH`` or the command fails.

    Args:
        code (str): The generated Python source.

    Returns:
        str: The formatted source, or the original string if formatting is skipped.
    """

    if not shutil.which("ruff"):
        logger.warning("ruff not found; skipping formatting")
        return code
    try:
        result = subprocess.run(
            ["ruff", "format", "--stdin-filename", "decoder.py", "-"],
            input=code,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.warning("ruff format failed: %s", e.stderr.strip())
        return code


def _merge_members(existing: list[str], new: list[str]) -> list[str]:
    """Merge two member lists, preserving order and adding unseen names at the end.

    Args:
        existing: Already-collected member names for the struct.
        new: Member names from another encoding of the same instruction.

    Returns:
        Merged list with each name appearing once, in stable order.
    """
    return list(dict.fromkeys([*existing, *new]))


def _merge_member_types(
    existing: dict[str, ArmType | None], new: dict[str, ArmType | None]
) -> dict[str, ArmType | None]:
    """Merge the member types contributed by two encodings of one instruction.

    All encodings of an instruction share a single output struct, but they may type a
    member differently -- ``shift_n`` is ``bits1`` in one encoding of ``ADC_register``
    and ``bits6`` in another, ``d`` is a ``uint32`` register number in one form and a
    raw ``bits4`` field in another. ``join_types`` picks a type able to hold both (the
    wider width, the more specific interpretation).

    Args:
        existing: Already-collected member types for the struct.
        new: Member types contributed by another encoding.

    Returns:
        dict[str, ArmType | None]: Merged types; ``None`` where at least one encoding
        left the member's type undetermined.
    """

    merged: dict[str, ArmType | None] = dict(existing)
    for name, arm_type in new.items():
        if name not in merged:
            merged[name] = arm_type
            continue
        current = merged[name]
        merged[name] = join_types(current, arm_type) if current and arm_type else None
    return merged


def _field_extractions(bit_fields: list[dict], decoder_width: int) -> list[str]:
    """Generate operand field-extraction statements from a bit_fields list.

    The ``bit_fields`` entries are listed most-significant first and their widths sum
    to the encoding length. Each named ``field`` is extracted from the decoder-width,
    MSB-aligned instruction word. ``skip`` entries only advance the bit offset.

    Args:
        bit_fields (list[dict]): The encoding's ``bit_fields`` entries. Each entry has a
            ``width`` and either a ``field`` (operand name) or a ``skip`` (fixed bits).
        decoder_width (int): Target decoder width the instruction word is aligned to.

    Returns:
        list[str]: The extraction statements, in declaration order.
    """

    lines: list[str] = []
    offset = 0
    for bf in bit_fields:
        width = bf.get("width") if "field" in bf else bf["skip"]
        if "field" in bf:
            name = bf["field"]
            lsb = decoder_width - offset - width
            lines.append(f"{name} = _bits(instr, {lsb}, {width})")
        offset += width
    return lines


def _input_types(bit_fields: list[dict]) -> dict[str, ArmType]:
    """Map each named operand of an encoding to its ARM type.

    An encoded field is a raw bit vector as wide as the field itself, which is what
    ``arm-transpiller``'s type inference needs to size concatenations, bitwise masks
    and sign extensions.

    Args:
        bit_fields (list[dict]): The encoding's ``bit_fields`` entries.

    Returns:
        dict[str, ArmType]: Operand name to ``bits<width>``; ``skip`` entries are
        skipped.

    Example:
        >>> fields = [{"skip": 4}, {"width": 3, "field": "imm3"}]
        >>> _input_types(fields)
        {'imm3': ScalarType(kind='bits', width=3)}
    """

    return {bf["field"]: bits(int(bf["width"])) for bf in bit_fields if "field" in bf}


def _passthrough_operands(bit_fields: list[dict], program) -> list[str]:
    """Select the operand fields a ``decode`` block never turns into an output.

    A transpiled ``decode`` block produces the instruction's semantic operands (``d``,
    ``imm32``, ...), but some encoded fields never reach one of them and would be lost:

    * *unassigned inputs* -- read by the block, yet their value never flows into an
      assignment (e.g. ``firstcond`` and ``mask`` in ``IT``, which are only tested for
      UNPREDICTABLE cases), and
    * *unused fields* -- not mentioned by the block at all (e.g. ``option`` in ``DSB``
      or the coprocessor register numbers of ``MCR``).

    Both carry information a consumer of the decoded instruction needs, so they are
    added to the instruction object verbatim. ``arm-transpiller`` reports enum and
    constant tokens (``SRType_LSL``, ``TRUE``) as inputs too, so the candidates are
    restricted to the encoding's own ``bit_fields``.

    Args:
        bit_fields (list[dict]): The encoding's ``bit_fields`` entries.
        program: The parsed ``decode`` block (an ``arm-transpiller`` ``Program``).

    Returns:
        list[str]: Field names to add as members, in ``bit_fields`` order.
    """

    inputs = set(extract_input_variables(program))
    outputs = set(extract_output_variables(program))
    unassigned = set(extract_unassigned_inputs(program))

    return [
        bf["field"]
        for bf in bit_fields
        if "field" in bf
        and bf["field"] not in outputs
        and (bf["field"] in unassigned or bf["field"] not in inputs)
    ]


def _unbound_members(
    members: list[str], bit_fields: list[dict], program, input_types
) -> set[str]:
    """Select the members a leaf is not guaranteed to have bound before it returns.

    ``arm-transpiller`` reports which output variables a ``decode`` block leaves
    unassigned on some path -- ``VMOV_immediate`` assigns ``imm32`` or ``imm64``
    depending on ``dp_operation``, and either one would be an unbound local on the
    other path. The analysis is exact rather than syntactic: it uses the inferred type
    of a ``case`` selector to decide exhaustiveness, so the four ``when`` arms of
    ``VRINTA_VRINTN_VRINTP_VRINTM`` do bind ``rmode``/``away``.

    Operands are extracted unconditionally at the top of the leaf, so a member that is
    one of the encoding's own ``bit_fields`` is always bound.

    Args:
        members (list[str]): The member names of this encoding.
        bit_fields (list[dict]): The encoding's ``bit_fields`` entries.
        program: The parsed ``decode`` block (an ``arm-transpiller`` ``Program``).
        input_types (dict[str, ArmType]): The encoding's operand field types, which the
            analysis needs to size the values a ``case`` selector can take.

    Returns:
        set[str]: Members needing a value before the transpiled block runs.
    """

    conditional = set(extract_conditionally_assigned(program, input_types))
    operands = {bf["field"] for bf in bit_fields if "field" in bf}
    return (conditional & set(members)) - operands


def _member_types(
    members: list[str],
    program,
    input_types: dict[str, ArmType],
    leaf_name: str,
) -> dict[str, ArmType | None]:
    """Determine the ARM type of every member an encoding contributes.

    ``arm-transpiller`` infers a width-carrying type for each variable a ``decode``
    block defines (``d`` is a ``uint32`` register number, ``imm32`` a ``bits32``
    immediate, ``setflags`` a ``bool``) and answers for the operands it was handed too,
    so pass-through members that the block never assigns (``option`` in ``DSB``,
    ``cond`` in ``B`` T1/T3) are typed by the same call. ``infer_types`` needs no
    ``generate()`` beforehand, so typing an encoding does not depend on having
    transpiled it.

    A type stays undetermined when the block calls a function the runtime does not
    declare or reads a constant that is neither a ``bit_fields`` entry nor listed in
    ``arm-transpiller``'s known-types table; that is worth a warning, since such a
    block also references a name the embedded runtime does not define.

    Args:
        members (list[str]): The member names of this encoding, in emission order.
        program: The parsed ``decode`` block (an ``arm-transpiller`` ``Program``).
        input_types (dict[str, ArmType]): The encoding's operand field types; these win
            over ``arm-transpiller``'s global name table, which is what keeps a field
            at the width its own encoding gives it.
        leaf_name (str): Name of the encoding, used for the warning only.

    Returns:
        dict[str, ArmType | None]: Member name to type, ``None`` where undetermined.
    """

    inferred = infer_types(program, input_types)
    types: dict[str, ArmType | None] = {}
    for member in members:
        arm_type = inferred.get(member)
        if arm_type is None:
            logger.warning("%s: cannot determine the type of '%s'", leaf_name, member)
        types[member] = arm_type
    return types


def _analyse_encoding(
    instr, encoding, decoder_width: int, length_bytes: int, length_bits: int
) -> dict:
    """Transpile and analyse a single instruction encoding.

    Transpiles the ARM pseudocode ``decode`` block to Python via ``arm-transpiller``
    and derives everything the leaf body is assembled from. Emission is a separate step
    (:func:`_build_leaf`): a leaf has to satisfy the member set of the *whole*
    instruction, which is only known once every encoding has been analysed.

    Args:
        instr (dict): The parent instruction entry (provides ``id`` and ``mnemonic``).
        encoding (dict): The encoding entry (``name``, ``bit_fields``, ``decode`` ...).
        decoder_width (int): The target decoder width.
        length_bytes (int): The encoding's own length in bytes; the leaf returns it
            alongside the decoded instruction so the caller knows how far to advance.
        length_bits (int): The encoding's own bit length; used to set decoder state.

    Returns:
        dict: Analysis with keys ``name``, ``struct``, ``members``, ``member_types``,
        ``bound``, ``extractions``, ``decode_lines``, ``can_raise``,
        ``length_bytes`` and ``length_bits``.
    """

    # All encodings (T1, T2, ...) of one instruction share a single struct named
    # after the instruction id; the encoding form only matters for pattern matching.
    struct = instr["id"]
    name = f"{instr['id'].lower()}_{encoding['name'].lower()}"

    bit_fields = encoding.get("bit_fields", [])

    program = parse(encoding.get("decode", ""))
    # The same field name is a different width in different ARMv7-M encodings
    # (``Rd`` is 3 bits in the Thumb 16-bit high-register forms, 4 in the 32-bit
    # ones), so the encoding's own ``bit_fields`` type the transpiler's inputs rather
    # than arm-transpiller's global name table.
    input_types = _input_types(bit_fields)
    generator = PythonGenerator(input_types=input_types)
    decode_py = generator.generate(program)
    # Members are the variables the block assigns, plus the encoded fields it never
    # turns into one of them -- those would otherwise be dropped from the result.
    # Intermediates that the block splices verbatim into another output are left out:
    # ``I1``/``I2`` in ``B`` T4 are bits 23 and 22 of the ``imm32`` they help build, so
    # keeping them would duplicate information -- and would force the encodings that do
    # not compute them (``B`` T1/T2/T3) to invent a value.
    out_vars = extract_output_variables(program)
    subsumed = set(extract_subsumed_variables(program, input_types))
    members = _merge_members(
        [var for var in out_vars if var not in subsumed],
        _passthrough_operands(bit_fields, program),
    )
    member_types = _member_types(members, program, input_types, name)
    # ``extract_side_effects`` reports whether the block can flag a side effect --
    # SEE, UNDEFINED or UNPREDICTABLE -- either through an explicit statement or via a
    # runtime helper that raises one internally (e.g. ``ThumbExpandImm``). Any of the
    # three routes the return through ``_apply_sideeffect``.
    sideeffects = extract_side_effects(program)
    can_raise = (
        sideeffects["unpredictable"] or sideeffects["undefined"] or sideeffects["see"]
    )

    return {
        "name": name,
        "struct": struct,
        "members": members,
        "member_types": member_types,
        "operands": {bf["field"] for bf in bit_fields if "field" in bf},
        "unbound": _unbound_members(members, bit_fields, program, input_types),
        "extractions": _field_extractions(bit_fields, decoder_width),
        "decode_lines": decode_py.splitlines(),
        "can_raise": can_raise,
        "length_bytes": length_bytes,
        "length_bits": length_bits,
    }


def _build_leaf(
    analysis: dict,
    struct_types: dict[str, ArmType | None],
    decoder_width: int,
    backend: PythonGenerator,
) -> dict:
    """Assemble the leaf body executed once an encoding matches.

    Every member of an instruction is required, so the leaf has to hand the constructor
    a value for each one. Two groups need a value the ``decode`` block never produces
    and are pre-set to the zero of their type:

    * members another encoding of the same instruction contributes but this one does
      not (``B`` gains ``cond`` from T1/T3 and ``I1``/``I2`` from T4, so T2 supplies
      all three), and
    * members the block assigns on some paths only (``VMOV_immediate`` assigns
      ``imm32`` or ``imm64`` depending on ``dp_operation``), which would otherwise be
      unbound locals.

    Args:
        analysis (dict): The encoding's analysis, as returned by
            :func:`_analyse_encoding`.
        struct_types (dict[str, ArmType | None]): The member types of the instruction's
            struct, merged over all its encodings; the keys are the full member set in
            emission order.
        decoder_width (int): The target decoder width.
        backend (PythonGenerator): The generator for the output language; it spells the
            zero value a member of a given ARM type is pre-set to.

    Returns:
        dict: Leaf metadata with keys ``name``, ``struct``, ``members`` and ``body``.
    """

    members = list(struct_types)
    # A member this encoding does not produce but does extract as an operand needs no
    # value of its own (T2 of the ``FOO`` fixture consumes ``a`` into ``x``, while T1
    # passes ``a`` through, so the struct has both and T2's extracted ``a`` fills the
    # member).
    absent = [
        member
        for member in members
        if member not in analysis["members"] and member not in analysis["operands"]
    ]
    unbound = [member for member in members if member in analysis["unbound"]]

    body: list[str] = []
    if analysis["extractions"]:
        body.append("# operands")
        body.extend(analysis["extractions"])
    if absent:
        body.append("# members this encoding does not produce")
        body.extend(f"{m} = {backend.zero_value(struct_types[m])}" for m in absent)
    if unbound:
        body.append("# members a branch may leave unassigned")
        body.extend(f"{m} = {backend.zero_value(struct_types[m])}" for m in unbound)
    if analysis["decode_lines"]:
        body.append("# decode")
        body.extend(analysis["decode_lines"])

    length_bytes = analysis["length_bytes"]
    length_bits = analysis["length_bits"]
    if length_bits == 8:
        decoder_state = "DecoderState.DECODED_8BIT"
    elif length_bits == 16:
        decoder_state = "DecoderState.DECODED_16BIT"
    elif length_bits == 32:
        decoder_state = "DecoderState.DECODED_32BIT"
    else:
        decoder_state = "DecoderState.DECODER_NONE"
    body.append(f"decoder_state = {decoder_state}")

    args = ", ".join(f"{member}={member}" for member in members)
    if args:
        args = f"{args}, decoder_state=decoder_state"
    else:
        args = "decoder_state=decoder_state"
    struct_call = f"{analysis['struct']}({args})"
    # ``decode`` returns ``(result, n_bytes)`` so the caller can advance without a
    # separate size pass; the length is a literal known from this encoding's pattern.
    if analysis["can_raise"]:
        # A flagged side effect replaces the decoded instruction with an
        # Undefined/Unpredictable pseudo-instruction; only wrap the blocks that
        # can actually raise one.
        body.append(
            f"return _apply_sideeffect(ctx, {struct_call}), {length_bytes}"
        )
    else:
        body.append(f"return {struct_call}, {length_bytes}")

    return {
        "name": analysis["name"],
        "struct": analysis["struct"],
        "members": members,
        "body": "\n".join(body),
    }


def _load(input_yaml: str, decoder_width: int):
    """Parse the instruction-set YAML and build the pattern/struct repositories.

    Args:
        input_yaml (str): YAML in the ``instructions``/``encodings`` format.
        decoder_width (int): The target decoder width.

    Returns:
        tuple: ``(pat_repo, structs, struct_id_map)`` where ``pat_repo`` maps each
        ``BitPattern`` to its leaf metadata, ``structs`` is the de-duplicated output
        dataclass list (each member carrying its Python annotation and the ARM type it
        was inferred from), and ``struct_id_map`` maps struct names to enumerated IDs.
    """

    ins = yaml.load(input_yaml, Loader=yaml.Loader)
    if ins is None:
        ins = {}
    instructions = ins.get("instructions", []) or []

    struct_id_map: dict[str, int] = {}
    for instr in instructions:
        for encoding in instr.get("encodings", []):
            struct = instr["id"]
            if struct not in struct_id_map:
                struct_id_map[struct] = len(struct_id_map)

    # One struct per instruction; its members are contributed by all encodings, so both
    # the member set and their types are merged encoding by encoding (insertion order
    # is the emission order). Analysis and emission are therefore two passes: a leaf
    # has to supply every member of its instruction, including the ones only a sibling
    # encoding produces, which is not known until all of them have been analysed.
    analyses: list[tuple[BitPattern, dict]] = []
    structs: dict[str, dict[str, ArmType | None]] = {}
    for instr in instructions:
        for encoding in instr.get("encodings", []):
            pat = BitPattern.parse_pattern(str(encoding["pattern"]))
            length_bytes = int(ceil(pat.bit_length / 8))
            analysis = _analyse_encoding(
                instr, encoding, decoder_width, length_bytes, pat.bit_length
            )
            analyses.append((pat, analysis))
            existing = structs.get(analysis["struct"], {})
            structs[analysis["struct"]] = _merge_member_types(
                existing, analysis["member_types"]
            )

    # How an ARM value is spelled in the generated decoder -- its type annotation and
    # the zero it is pre-set to -- belongs to the backend for the output language, not
    # to decoder-forge. Both are pure functions of the type, so one instance serves the
    # whole run and needs no ``generate()`` call of its own.
    backend = PythonGenerator()

    pat_repo: dict[BitPattern, dict] = {
        pat: _build_leaf(analysis, structs[analysis["struct"]], decoder_width, backend)
        for pat, analysis in analyses
    }

    struct_list = [
        {
            "name": name,
            "members": [
                {
                    "name": member,
                    "annotation": backend.type_annotation(arm_type),
                    "arm_type": str(arm_type) if arm_type is not None else None,
                }
                for member, arm_type in member_types.items()
            ],
        }
        for name, member_types in structs.items()
    ]
    return pat_repo, struct_list, struct_id_map


def generate_code(input_yaml, decoder_width, tengine, printer, auto_format=True):
    """Generate and output decoder code from an ARMv7-M instruction-set YAML string.

    The input uses the ``instructions``/``encodings`` format: each encoding provides a
    match ``pattern`` and an ARM pseudocode ``decode`` block. Patterns are organised
    into a decode tree, while the ``decode`` blocks are transpiled to Python via
    ``arm-transpiller`` and emitted as the per-encoding leaf bodies. Each leaf also
    returns its own byte length, so variable-length instructions need no separate size
    pass.

    When ``auto_format`` is ``True``, the generated source is formatted with ``ruff
    format`` before being written to the printer.

    Args:
        input_yaml (str): A YAML string with an ``instructions`` list.
        decoder_width (int): The bit width used when constructing the decode tree.
        tengine (ITemplateEngine): A template engine instance used to generate code.
        printer: Writable stream with a ``write(str)`` method.
        auto_format (bool): Whether to run ``ruff format`` on the generated code
            (default ``True``).

    Raises:
        yaml.YAMLError: If the input YAML cannot be parsed.
        ValueError: If a pattern is wider than ``decoder_width``.
    """

    logger.info("Call: generate_code")

    pat_repo, structs, struct_id_map = _load(input_yaml, decoder_width)

    pats = list(pat_repo.keys())
    uid_to_pat, _, pats_with_uid = assign_uids(pats)

    # only build decode tree when patterns are assigned
    if len(pats_with_uid) != 0:
        max_decoder_bits = max((i.bit_length for i in pats))
        min_decoder_bits = min((i.bit_length for i in pats))

        if max_decoder_bits > decoder_width:
            raise ValueError("Patterns are too long for given decoder width")

        decode_tree = build_decode_tree_by_fixed_bits(
            pats_with_uid, decoder_width=decoder_width
        )
        flat_decode_tree = flatten_decode_tree(decode_tree)
    else:
        decoder_width = 0
        max_decoder_bits = 0
        min_decoder_bits = 0

        decode_tree = None
        flat_decode_tree = list()

    # ``decode`` reports the length of each matched instruction directly (each leaf
    # returns it as a literal), so no separate size decoder is generated. The caller
    # reads up to ``needed_bytes_for_code_eval`` bytes and, on a no-match, advances by
    # the smallest possible instruction (``min_instr_bytes``).
    needed_bytes_for_code_eval = int(ceil(decoder_width / 8))
    min_instr_bytes = max(1, int(ceil(min_decoder_bits / 8)))

    tengine.load("python")

    # The transpiled leaves call into ``arm-transpiller``'s runtime (``UInt``,
    # ``concat_bits``, ``ThumbExpandImm``, ...), which the template embeds verbatim so
    # the generated decoder is self-contained. The package hands out the source for the
    # target language, so decoder-forge keeps no copy of it.
    context = {
        "armruntime": get_runtime_source("python"),
        "pat_repo": pat_repo,
        "structs": structs,
        "struct_id_map": struct_id_map,
        "uid_to_pat": uid_to_pat,
        "flat_decode_tree": flat_decode_tree,
        "needed_bytes_for_code_eval": needed_bytes_for_code_eval,
        "min_instr_bytes": min_instr_bytes,
    }
    rendered_code = tengine.generate(context)

    if auto_format:
        rendered_code = _format_code(rendered_code)

    for i in rendered_code.splitlines():
        printer.write(i + "\n")
