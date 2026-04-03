import utils
import constants
import jinja2
import cambc
import builtins
import random
import sys
from pathlib import Path
import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    "--prod",
    action="store_true",
    help="Run in production mode (LOCAL = False)",
)
args = parser.parse_args()

env = jinja2.Environment(
    loader=jinja2.FileSystemLoader("../Awubot/"),
    trim_blocks=True,
    lstrip_blocks=True,
)
env.globals["LOCAL"] = not args.prod

env.globals.update(vars(builtins))
env.globals.update({name: getattr(cambc, name)
                   for name in dir(cambc) if not name.startswith("_")})
env.globals.update({
    "random": random,
})
utils.register(env)
constants.register(env)


def render(template_dir=Path("..") / "Awubot"):
    output_dir = Path("..") / "Generated"

    for src in template_dir.rglob("*.pyj2"):
        relative = src.relative_to(template_dir)
        dest_rel = relative.with_suffix(".py")
        dest = output_dir / dest_rel

        template = env.get_template(str(relative))
        rendered = template.render()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(rendered)


render()
