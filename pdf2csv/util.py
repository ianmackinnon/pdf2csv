# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Utility functions for pdf2svg.
"""

import shutil
import logging
import tempfile



LOG = logging.getLogger('util')



DEFAULT_SVG_WIDTH = 100
DEFAULT_SVG_HEIGHT = 100
DEFAULT_SVG_UNIT = "mm"



def color_log(log):
    color_red = '\033[91m'
    color_green = '\033[92m'
    color_yellow = '\033[93m'
    color_blue = '\033[94m'
    color_end = '\033[0m'

    level_colors = (
        ("error", color_red),
        ("warning", color_yellow),
        ("info", color_green),
        ("debug", color_blue),
    )

    safe = None
    color = None

    def xor(a, b):
        return bool(a) ^ bool(b)

    def _format(value):
        if isinstance(value, float):
            return "%0.3f"
        else:
            return "%s"

    def message_args(args):
        if not args:
            return "", []
        if (
                not isinstance(args[0], str) or
                xor(len(args) > 1, "%" in args[0])
        ):
            return " ".join([_format(v) for v in args]), args
        return args[0], args[1:]

    def _message(args, color):
        message, args = message_args(args)
        return "".join([color, message, color_end])

    def _args(args):
        args = message_args(args)[1]
        return args

    def build_lambda(safe, color):
        return lambda *args, **kwargs: getattr(log, safe)(
            _message(args, color), *_args(args), **kwargs)

    for (level, color) in level_colors:
        safe = "%s_" % level
        setattr(log, safe, getattr(log, level))
        setattr(log, level, build_lambda(safe, color))



def dump_svg(path, items, x=None, y=None, width=None, height=None, unit=None):
    LOG.debug("Writing SVG with %s items to %s.", len(items), path)

    if width is None:
        width = DEFAULT_SVG_WIDTH
    if height is None:
        height = DEFAULT_SVG_HEIGHT
    if unit is None:
        unit = DEFAULT_SVG_UNIT

    header = """\
<svg
  xmlns:svg="http://www.w3.org/2000/svg"
  xmlns="http://www.w3.org/2000/svg"
  xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
  xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
  width="{width}{unit}"
  height="{height}{unit}"
  viewBox="{x} {y} {width} {height}"
>
  <sodipodi:namedview
    inkscape:document-units="{unit}"
    units="{unit}"
  />
  <g transform="matrix(1, 0, 0, -1, 0, {height})">
""".format(**{
    "x": 0,
    "y": 0,
    "width": width,
    "height": height,
    "unit": unit,
})

    footer = """\
  </g>
</svg>
"""

    with tempfile.NamedTemporaryFile(
        delete=False, mode="w+", encoding="utf-8"
    ) as temp:

        temp.write(header)

        for item in items:
            tag = item.pop("tag")
            layer = item.pop("layer")
            if tag in ("rect", "line"):
                attrs = " ".join(['%s="%s"' % (k, v) for k, v in item.items()])
                temp.write("    <%s %s></%s>\n" % (tag, attrs, tag))
            else:
                LOG.warning("Ignoring unrecognized SVG item with tag '%s'.", tag)

        temp.write(footer)

        temp.close()
        shutil.move(temp.name, path)
