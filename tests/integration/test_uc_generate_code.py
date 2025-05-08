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
    uc_generate_code(printer_mock, tengine, yaml_buf, decoder_width=8)

    generated_code = extract_generated_code(printer_mock)

    # execute the code
    test_namespace = {}
    exec(generated_code, test_namespace)

    context = test_namespace["Context"]()

    # call the decoder
    decode_output = test_namespace["decode"](0xFF, context)

    # returns undef class
    assert decode_output == test_namespace["Undef"](code=0xFF)


def test_uc_generate_code_generate_and_eval_python_code_test_format_returns_structD():
    printer_mock = Mock(spec=IPrinter)
    tengine = TemplateEngine()

    # method under test
    test_format = files("tests.data.formats").joinpath("test-format.yaml").read_text()
    uc_generate_code(printer_mock, tengine, test_format, decoder_width=8)

    generated_code = extract_generated_code(printer_mock)

    # execute the code
    test_namespace = {}
    exec(generated_code, test_namespace)

    context = test_namespace["Context"]()
    # call the decoder
    decode_output = test_namespace["decode"](0x1F, context)
    assert decode_output == test_namespace["StructD"](rd0=0x3)


def test_uc_generate_code_generate_and_eval_python_code_test_context_updated():
    printer_mock = Mock(spec=IPrinter)
    tengine = TemplateEngine()

    # method under test
    test_format = files("tests.data.formats").joinpath("test-format.yaml").read_text()
    uc_generate_code(printer_mock, tengine, test_format, decoder_width=8)

    generated_code = extract_generated_code(printer_mock)

    # execute the code
    test_namespace = {}
    exec(generated_code, test_namespace)

    context = test_namespace["Context"]()

    assert context.context1 == 0x0

    # call the decoder
    _ = test_namespace["decode"](code=0x40, context=context)

    assert context.context1 == 0xCAFE
