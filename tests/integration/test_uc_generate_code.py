from decoder_forge.external.template_engine import TemplateEngine
from decoder_forge.uc_generate_code import uc_generate_code
from unittest.mock import Mock
from decoder_forge.i_printer import IPrinter
from importlib.resources import files


def extract_generated_code(printer_mock: Mock):
    # call[0] is the list of positional arg, call[0][0] is the first positional arg
    generated_code = [call[0][0] for call in printer_mock.print.call_args_list]

    # generated code is in a list ... join it to get a string
    generated_code_str = "\n".join(generated_code)

    return generated_code_str


def test_uc_generate_code_generate_and_eval_python_code_empty_format_outputs_None():
    yaml_buf = ""
    printer_mock = Mock(spec=IPrinter)
    tengine = TemplateEngine()

    # method under test
    uc_generate_code(printer_mock, tengine, yaml_buf)

    generated_code = extract_generated_code(printer_mock)

    # execute the code
    test_namespace = {}
    exec(generated_code, test_namespace)

    # call the decoder
    decode_output = test_namespace["decode"](0xFF)
    assert decode_output is None


def test_uc_generate_code_generate_and_eval_python_code_test_format_outputs_None():
    printer_mock = Mock(spec=IPrinter)
    tengine = TemplateEngine()

    # method under test
    test_format = files("tests.data.formats").joinpath("test-format.yaml").read_text()
    uc_generate_code(printer_mock, tengine, test_format)

    generated_code = extract_generated_code(printer_mock)

    # execute the code
    test_namespace = {}
    exec(generated_code, test_namespace)

    # call the decoder
    decode_output = test_namespace["decode"](0x0F)
    assert decode_output == "instr_E0"
