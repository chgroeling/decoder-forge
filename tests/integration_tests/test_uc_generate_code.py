from decoder_forge.external.template_engine import TemplateEngine
from decoder_forge.uc_generate_code import uc_generate_code
from unittest.mock import Mock
from decoder_forge.i_printer import IPrinter


def test_uc_generate_code_generate_and_eval_python_code_empty_patterns_outputs_None():
    printer = Mock(spec=IPrinter)
    tengine = TemplateEngine()
    json_buf = "{}"

    uc_generate_code(printer, tengine, json_buf)

    # call[0] is the list of positional arg, call[0][0] is the first positional arg
    generated_code = [
        call[0][0] for call in printer.print.call_args_list
    ]

    # generated code is in a list ... join it to get a string
    generated_code = "\n".join(generated_code)

    # execute the code
    test_namespace = {}
    exec(generated_code, test_namespace)

    # call the decoder
    decode_output = test_namespace["decode"](0xFF)
    assert decode_output is None
