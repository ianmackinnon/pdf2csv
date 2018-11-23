#!/usr/bin/env python3

import csv
import sys
import logging
import argparse
import unittest

sys.path.append("../")

from pdf2csv import pdf_to_csv_tables



LOG = logging.getLogger("test_pdf2csv")



class TestClass(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.longMessage = True

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def compare_known_result(self, name):
        pdf_path = "cases/{name}.pdf".format(name=name)
        csv_known_path = "cases/{name}.csv".format(name=name)

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



def main():
    LOG.addHandler(logging.StreamHandler())

    parser = argparse.ArgumentParser(description="test_known_results.")
    parser.add_argument(
        "--verbose", "-v",
        action="count", default=0,
        help="Print verbose information for debugging.")
    parser.add_argument(
        "--quiet", "-q",
        action="count", default=0,
        help="Suppress warnings.")

    args = parser.parse_args()

    level = (logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG)[
        max(0, min(3, 1 + args.verbose - args.quiet))]
    LOG.setLevel(level)

    unittest.main()



if __name__ == "__main__":
    main()