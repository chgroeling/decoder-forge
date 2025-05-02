from jinja2 import Environment
from jinja2 import PackageLoader
from jinja2.utils import select_autoescape

from decoder_forge.i_template_engine import ITemplateEngine


class TemplateEngine(ITemplateEngine):
    def __init__(self):
        self._env = Environment(
            loader=PackageLoader("decoder_forge"), autoescape=select_autoescape()
        )

    def load(self, template_key):
        # has currently no function other than loading the python template
        self._template = self._env.get_template("python_decoder.py.jinja")

    def generate(self, context):
        return self._template.render(**context)
