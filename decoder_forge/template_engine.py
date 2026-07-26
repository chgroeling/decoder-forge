from typing import Protocol

from jinja2 import Environment
from jinja2 import PackageLoader
from jinja2.utils import select_autoescape


class ITemplateEngine(Protocol):
    def load(self, template_key: str) -> None: ...
    def generate(self, context: dict) -> str: ...


class TemplateEngine:
    def __init__(self):
        self._env = Environment(
            loader=PackageLoader("decoder_forge"), autoescape=select_autoescape()
        )

    def load(self, template_key):
        self._template = self._env.get_template("python_decoder.py.jinja")

    def generate(self, context):
        return self._template.render(**context)
