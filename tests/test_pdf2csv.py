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

import os
import csv
import sys
import argparse
import unittest
from subprocess import Popen, PIPE

sys.path.append("../")

from pdf2csv import pdf_to_csv_tables



TEST_PATH = os.path.abspath(os.path.dirname(__file__))



class TestApi(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.longMessage = True

    def compare_known_result(self, name):
        pdf_path = os.path.join(TEST_PATH, "cases/{name}.pdf".format(name=name))
        csv_known_path = os.path.join(TEST_PATH, "cases/{name}.csv".format(name=name))

        with open(csv_known_path) as fp:
            reader = csv.reader(fp)
            known_rows = [[v or None for v in row] for row in reader]

        kwargs = {
            "border_width": 1.5,
        }

        test_rows = []
        for t, table in enumerate(pdf_to_csv_tables(pdf_path, **kwargs)):
            if t:
                test_rows.append([])
            for row in table:
                test_rows.append(row)

        self.assertEqual(len(known_rows), len(test_rows))
        self.assertEqual(known_rows, test_rows)

    def test_eu_20th_204(self):
        name = "eu-20th-204"
        self.compare_known_result(name)

    def test_eu_20th_333(self):
        name = "eu-20th-333"
        self.compare_known_result(name)

    def test_eu_20th_1020(self):
        name = "eu-20th-1020"
        self.compare_known_result(name)



class TestCli(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.longMessage = True

    def compare_known_result(self, name):
        pdf_path = os.path.join(TEST_PATH, "cases/{name}.pdf".format(name=name))
        csv_known_path = os.path.join(TEST_PATH, "cases/{name}.csv".format(name=name))
        svg_known_path = os.path.join(TEST_PATH, "cases/{name}.0001.svg".format(name=name))
        csv_test_path = "/tmp/{name}.csv".format(name=name)
        svg_test_path = "/tmp/{name}.%04d.svg".format(name=name)

        try:
            os.remove(csv_test_path)
        except FileNotFoundError:
            pass
        try:
            os.remove(svg_test_path)
        except FileNotFoundError:
            pass

        border_width = 1.5

        cmd = [
            "pdf2csv",
            "--border-width", str(border_width),
            "--debug-dump-svg-path", svg_test_path,
            "-o", csv_test_path,
            pdf_path,
        ]
        process = Popen(cmd, stdout=PIPE, stderr=PIPE)
        (out, err) = process.communicate()
        status = process.returncode
        self.assertFalse(out)
        self.assertFalse(err)
        self.assertFalse(status)

        cmd = [
            "diff", "-q",
            csv_known_path,
            csv_test_path,
        ]
        process = Popen(cmd, stdout=PIPE, stderr=PIPE)
        (out, err) = process.communicate()
        status = process.returncode
        self.assertFalse(out)
        self.assertFalse(err)
        self.assertFalse(status)

        cmd = [
            "diff", "-q",
            svg_known_path,
            svg_test_path % 1,
        ]
        process = Popen(cmd, stdout=PIPE, stderr=PIPE)
        (out, err) = process.communicate()
        status = process.returncode
        self.assertFalse(out)
        self.assertFalse(err)
        self.assertFalse(status)

    def test_eu_20th_204(self):
        name = "eu-20th-204"
        self.compare_known_result(name)

    def test_eu_20th_333(self):
        name = "eu-20th-333"
        self.compare_known_result(name)

    def test_eu_20th_1020(self):
        name = "eu-20th-1020"
        self.compare_known_result(name)
