#!/usr/bin/env python3

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
pdf2csv

Extract tabular data from PDF files by detecting table border lines.
"""

import re
import csv
import sys
import shutil
import logging
import argparse
import tempfile
import collections

from pdfminer.pdfparser import PDFParser
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
from pdfminer.layout import LAParams, \
    LTTextBoxHorizontal, LTTextBoxVertical, LTTextLine, LTChar, LTAnno, \
    LTRect, LTLine
from pdfminer.converter import PDFPageAggregator

from .util import color_log, dump_svg



LOG = logging.getLogger('pdf2csv')



MAX_SPLIT_ITERATIONS = 1e5
MAX_GROUP_ITERATIONS = 1e7
DEFAULT_BORDER_WIDTH = 1
SVG_CONTENT_OPTIONS = (
    "char",
    "geo",
    "bbox",
    "split",
)

DEBUG_GROUPING = False
DEBUG_SPLITS = False



def geo_to_tables(group_list, border_width=None, debug_svg=None):
    def line_to_bbox(line):
        if isinstance(line["x"], collections.abc.Iterable):
            return {
                "x": list(line["x"]),
                "y": [line["y"], line["y"]],
            }
        return {
            "x": [line["x"], line["x"]],
            "y": list(line["y"]),
        }

    def segment_touch(segment1, segment2, overlap=None):
        if overlap is None:
            overlap = DEFAULT_BORDER_WIDTH
        return (
            segment1[0] - overlap <= segment2[0] <= segment1[1] + overlap or
            segment1[0] - overlap <= segment2[1] <= segment1[1] + overlap or
            segment2[0] - overlap <= segment1[0] <= segment2[1] + overlap or
            segment2[0] - overlap <= segment1[1] <= segment2[1] + overlap
        )

    def bbox_touch(bbox1, bbox2, overlap=None):
        return (
            segment_touch(bbox1["x"], bbox2["x"], overlap) and
            segment_touch(bbox1["y"], bbox2["y"], overlap)
        )

    def bbox_combine(bbox1, bbox2):
        def segment_combine(segment1, segment2):
            points = list(segment1) + list(segment2)
            return [min(points), max(points)]

        return {
            "x": segment_combine(bbox1["x"], bbox2["x"]),
            "y": segment_combine(bbox1["y"], bbox2["y"]),
        }

    i = 0
    LOG.debug("Combining groups...")
    while True:
        i += 1
        if i > MAX_GROUP_ITERATIONS:
            LOG.error("Maximum grouping iterations (%d) reached.", MAX_GROUP_ITERATIONS)
            sys.exit(1)

        if DEBUG_GROUPING:
            LOG.debug("%d groups", len(group_list))

        if len(group_list) < 2:
            break

        for g1, group1 in enumerate(group_list[:-1]):
            for g2, group2 in enumerate(group_list[g1 + 1:], g1 + 1):
                touch = bbox_touch(
                    group1["bbox"], group2["bbox"], overlap=border_width)
                if touch:
                    group1["lines"] += group2["lines"]
                    group1["bbox"] = bbox_combine(group1["bbox"], group2["bbox"])
                    group_list.pop(g2)
                    if DEBUG_GROUPING:
                        LOG.debug("Move group %s into group %d. %d lines",
                                  g2, g1, len(group1["lines"]))
                    break # Matches found: break for g2
            else:
                continue
            break # Matches found: break for g1
        else:
            break # No matches found: break while True

    tables = []

    for g, group in enumerate(group_list):
        width = group["bbox"]["x"][1] - group["bbox"]["x"][0]
        height = group["bbox"]["y"][1] - group["bbox"]["y"][0]
        table = {
             "x_lines": [],
             "y_lines": [],
        }
        ignore = width < border_width or height < border_width
        LOG.debug("Group: %d lines: %.3fx%.3f%s", len(group["lines"]),
                  width, height, " ignoring" if ignore else "")
        if ignore:
            continue

        for line in group["lines"]:
            if isinstance(line["x"], collections.abc.Iterable):
                table["x_lines"].append(line)
            else:
                table["y_lines"].append(line)

        table["x_lines"].sort(key=lambda line: (line["y"], line["x"]))
        table["y_lines"].sort(key=lambda line: (line["x"], line["y"]))

        table.update({
            "bbox": group["bbox"]
        })

        tables.append(table)

        if debug_svg:
            debug_svg["items"].append({
                "tag": "rect",
                "layer": "table",
                "style": "fill: #884444; fill-opacity: 0.25;",
                "x": group["bbox"]["x"][0],
                "y": group["bbox"]["y"][0],
                "width": group["bbox"]["x"][1] - group["bbox"]["x"][0],
                "height": group["bbox"]["y"][1] - group["bbox"]["y"][0],
            })

    return tables



def scrape_page_data(
        page,
        border_width=None,
        breadcrumbs=None,
        debug_svg=None
):
    resource_manager = PDFResourceManager()
    la_params = LAParams()
    device = PDFPageAggregator(resource_manager, laparams=la_params)
    interpreter = PDFPageInterpreter(resource_manager, device)

    interpreter.process_page(page)
    layout = device.get_result()

    page_chars = []
    page_groups = []

    for element in layout:
        if isinstance(element, LTRect):
            page_groups.append({
                "bbox": {
                    "x": (element.x0, element.x1),
                    "y": (element.y0, element.y1),
                },
                "lines": [
                    {
                        "x": (element.x0, element.x1),
                        "y": element.y0,
                    },
                    {
                        "x": (element.x0, element.x1),
                        "y": element.y1,
                    },
                    {
                        "x": element.x0,
                        "y": (element.y0, element.y1),
                    },
                    {
                        "x": element.x1,
                        "y": (element.y0, element.y1),
                    }
                ]
            })
        elif isinstance(element, LTLine):
            LOG.warning("Line extraction not implemented yet")
        elif isinstance(element, LTTextBoxVertical):
            LOG.warning("Ignoring vertical text box")
        elif isinstance(element, LTTextBoxHorizontal):
            for o in element._objs:
                if not isinstance(o, LTTextLine):
                    continue
                if not o.get_text().strip():
                    continue
                for c in o._objs:
                    if isinstance(c, LTAnno):
                        continue
                    page_chars.append({
                        "x0": c.x0,
                        "x1": c.x1,
                        "y0": c.y0,
                        "y1": c.y1,
                        "text": c.get_text(),
                        "fontname": c.fontname,
                        "size": c.size,
                        "matrix": c.matrix
                    })
        else:
            LOG.warning("unknown element: %s", str(element))

    tables = geo_to_tables(
        page_groups,
        border_width=border_width,
        debug_svg=debug_svg
    )

    return {
        "chars": page_chars,
        "tables": tables,
    }



def table_to_rows(
        table_data, chars,
        breadcrumbs=None,
        border_width=None,
        remove_outer=True, remove_empty=False,
        debug_svg=None,
):

    if border_width is None:
        border_width = DEFAULT_BORDER_WIDTH

    def sort_index(splits, p):
        for i, pn in enumerate(splits):
            if p < pn:
                return i
        return len(splits)

    def char_index(splits, char, p0, p1):
        i0 = sort_index(splits, p0)
        i1 = sort_index(splits, p1)

        if char["text"].strip() and i0 != i1:
            LOG.debug("Character %s crosses line", repr(char["text"]))

        return sort_index(splits, (p0 + p1) // 2)

    def filter_splits(splits):
        i = 0
        out = sorted(list(set(splits)))
        LOG.debug("Combining splits...")
        while True:
            if i > MAX_SPLIT_ITERATIONS:
                LOG.error("Maximum split iterations (%d) reached.", MAX_SPLIT_ITERATIONS)
                sys.exit(1)

            if len(out) < 2:
                break

            for s1, split1 in enumerate(out[:-1]):
                for s2, split2 in enumerate(out[s1 + 1:], s1 + 1):
                    touch = split2 - split1 <= border_width
                    if touch:
                        out[s1] = (split1 + split2) / 2
                        out.pop(s2)
                        if DEBUG_SPLITS:
                            LOG.debug("Move split %s (%.3f) into split %d (%.3f). %.3f",
                                      s2, split2, s1, split1, out[s1])
                        break # Matches found: break for s2
                else:
                    continue
                break # Matches found: break for s1
            else:
                break # No matches found: break while True

        return out

    x_splits = filter_splits([line["x"] for line in table_data["y_lines"]])
    y_splits = filter_splits([line["y"] for line in table_data["x_lines"]])

    if debug_svg:
        for x in x_splits:
            debug_svg["items"].append({
                "tag": "line",
                "layer": "split",
                "style": "stroke: #448844; stroke-opacity: 0.25; stroke-width: 0.5;",
                "x1": x,
                "x2": x,
                "y1": table_data["bbox"]["y"][0],
                "y2": table_data["bbox"]["y"][1],
            })
        for y in y_splits:
            debug_svg["items"].append({
                "tag": "line",
                "layer": "split",
                "style": "stroke: #448844; stroke-opacity: 0.25; stroke-width: 0.5;",
                "y1": y,
                "y2": y,
                "x1": table_data["bbox"]["x"][0],
                "x2": table_data["bbox"]["x"][1],
            })

    LOG.debug("X splits:", repr(x_splits))
    LOG.debug("Y splits:", repr(y_splits))

    rows = []

    if len(x_splits) < 2 or len(y_splits) < 2:
        return rows

    x_len = len(x_splits) + 1
    y_len = len(y_splits) + 1
    x_data = [not remove_empty] * x_len
    y_data = [not remove_empty] * y_len

    table = []
    for t in range(x_len * y_len):
        table.append([])

    for char in chars:
        x = char_index(x_splits, char, char["x0"], char["x1"])
        y = char_index(y_splits, char, char["y0"], char["y1"])
        t = y * x_len + x
        table[t].append(char)
        if char["text"].strip():
            x_data[x] = True
            y_data[y] = True

    if remove_outer:
        x_data[0] = False
        x_data[-1] = False
        y_data[0] = False
        y_data[-1] = False

    for y in range(y_len):
        if not y_data[y]:
            continue

        row = []
        for x in range(x_len):
            if not x_data[x]:
                continue

            t = y * x_len + x
            cell = table[t]
            text = None
            if cell:
                text = ""
                for char in cell:
                    text += char["text"]

                    if debug_svg:
                        debug_svg["items"].append({
                            "tag": "rect",
                            "layer": "char",
                            "style": "fill: #444488; fill-opacity: 0.25;",
                            "x": char["x0"],
                            "y": char["y0"],
                            "width": char["x1"] - char["x0"],
                            "height": char["y1"] - char["y0"],
                        })

            if text:
                text = text.strip()
            row.append(text)
        rows.append(row)

    return rows[::-1]



def pdf_to_csv_tables(
        pdf_path,
        page_first=None, page_last=None,
        border_width=None,
        debug_dump_svg_path=None,
):
    LOG.info("%s: Searching for pages...", pdf_path)

    breadcrumbs = (pdf_path, )

    with open(pdf_path, "rb") as fp:
        for p, page in enumerate(PDFPage.get_pages(fp), 1):
            if page_first is not None and p < page_first:
                continue
            if page_last is not None and p > page_last:
                break

            LOG.info("Page %d", p)
            debug_svg = None
            if debug_dump_svg_path:
                page_geometry = dict(zip(
                    ("x", "y", "width", "height"),
                    page.mediabox
                ))
                LOG.debug("Page geometry: %s", page_geometry)

                svg_path = debug_dump_svg_path
                if re.compile(r"%-?\d*d").search(svg_path):
                    svg_path = svg_path % p
                LOG.debug("Debug SVG path: %s", svg_path)

                debug_svg = {
                    "path": svg_path,
                    "items": [],
                }
                debug_svg.update(page_geometry)

            page_breadcrumbs = breadcrumbs + ("page %s" % p,)
            page_data = scrape_page_data(
                page,
                border_width=border_width,
                breadcrumbs=page_breadcrumbs,
                debug_svg=debug_svg
            )

            for table in page_data["tables"]:
                table_rows = table_to_rows(
                    table, page_data["chars"],
                    border_width=border_width,
                    breadcrumbs=page_breadcrumbs,
                    debug_svg=debug_svg
                )
                yield table_rows

            if debug_svg:
                dump_svg(**debug_svg)



def pdf_to_csv_stream(pdf_path, out, **kwargs):
    written = False
    for row in pdf_to_csv_rows(pdf_path, **kwargs):
        if table_rows:
            if written:
                out.write("\n")
            writer = csv.writer(out)
            writer.writerows(table_rows)
            written = True



def parse_page_range(text):
    """
    Parse a string representation of a page range and return Integer
    values for first and last page, either or both of which may be `None`.
    """

    if not text:
        return (None, None)

    text = text.strip()

    if not text:
        return (None, None)

    try:
        page = int(text)
    except ValueError:
        pass
    else:
        return (page, page)

    (first, last) = text.split("-")

    first = int(first)
    last = int(last)

    return (first, last)



def main():
    LOG.addHandler(logging.StreamHandler())
    log_util = logging.getLogger('util')
    for log in LOG, log_util:
        color_log(log)

    parser = argparse.ArgumentParser(
        description="Scrape tabular data from PDF tables.")

    parser.add_argument(
        "--verbose", "-v",
        action="count", default=0,
        help="Print verbose information for debugging.")
    parser.add_argument(
        "--quiet", "-q",
        action="count", default=0,
        help="Suppress warnings.")

    parser.add_argument(
        "--page-range", "-p",
        action="store",
        help="Page range, starting from 1. Eg.: `2-9`.")
    parser.add_argument(
        "--border-width", "-b",
        action="store",
        type=float, default=DEFAULT_BORDER_WIDTH,
        help="Width of table borders in page units.")

    parser.add_argument(
        "--debug-dump-svg-path",
        action="store",
        help=(
            "Path to SVG output file for debug purposes. "
            "Include %d to insert page numbers."
        ))

    parser.add_argument(
        "--outfile", "-o",
        action="store",
        help="Path to CSV output file.")

    parser.add_argument(
        "pdf",
        metavar="PDF",
        help="Path to PDF input file.")

    args = parser.parse_args()

    level = (logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG)[
        max(0, min(3, 1 + args.verbose - args.quiet))]
    for log in LOG, log_util:
        log.setLevel(level)

    (page_first, page_last) = parse_page_range(args.page_range)

    def f(out):
        pdf_to_csv(
            args.pdf, out,
            page_first=page_first, page_last=page_last,
            border_width=args.border_width,
            debug_dump_svg_path=args.debug_dump_svg_path
        )

    if args.outfile:
        with tempfile.NamedTemporaryFile(
            delete=False, mode="w+", encoding="utf-8"
        ) as temp:
            f(temp)
            temp.close()
            shutil.move(temp.name, args.outfile)
    else:
        f(sys.stdout)



if __name__ == '__main__':
    main()
