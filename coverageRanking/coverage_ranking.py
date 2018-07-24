#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, re
from os.path import isfile, join
from subprocess import call
import subprocess
from pprint import pprint
import argparse

class coverageRanking():
    tests_by_class = {}

    # Pass in the package that you are covering and tests dir
    def __init__(self, cov_package, test_dir='test'):
        self.cov_package = cov_package
        self.test_dir = test_dir

    # Parses all unittest files in test_dir
    # Sets tests_by_class dict formatted like:
    #   { testFile: {testClass: [list, of ,test, names], ...}}
    def parseTests(self):
        test_classes = {}
        # For each test file in test dir
        test_files = [f for f in os.listdir(self.test_dir) if (isfile(join(self.test_dir, f)) and (re.search(r'^test_.*.py', f)))]
        for test_file in test_files:
            test_classes[test_file] = {}
            #Open file
            with (open(join(self.test_dir, test_file), 'r')) as fin:
                lines = fin.readlines()
            class_name = None
            for line in lines:
                if (re.search(r'^class\s+(.+)\(',line)):
                    class_name = re.search(r'^class\s+(.+)\(',line).group(1)
                    test_classes[test_file][class_name] = []
                elif ((class_name is not None) and (re.search(r'^\s\s\s\sdef\s+(test.+)\(',line))):
                    test_classes[test_file][class_name].append(re.search(r'^\s\s\s\sdef\s+(test.+)\(',line).group(1))
        self.tests_by_class = test_classes

    # Runs each test in tests_by_class & records line coverage
    def runTests(self):
        call(['cd', self.test_dir])
        call(['mkdir', 'covData'])
        for test_file, test_classes in self.tests_by_class.items():
            for test_class, test_list in test_classes.items():
                for test in test_list:
                    # Run test with coverage
                    # py.test --cov=pyllist test/test_pyllist.py::testdllist::test_init_empty
                    command = 'py.test --cov-report term-missing --cov=' + self.cov_package + ' ' \
                            + test_file + '::' + test_class + '::' + test 
                    cov_report = subprocess.run(command.split(' '), stdout=subprocess.PIPE)
                    self.parseCovReport(cov_report.stdout.decode('utf-8'))
                    # Copy coverage to named data file
                    new_cov_file = '.coverage.' + test_class + '.' + test
                    call(['mv', '.coverage', 'covData/'+new_cov_file])

    # Report Format: ['Name', 'Stmts', 'Miss', 'Cover', 'Missing']
    def parseCovReport(self, cov_report):
        self.file_coverage = {}
        lines = cov_report.split('\n')
        for line in lines:
            # If python file
            data = line.replace(', ', ',').split()
            if len(data):
                file_name = data[0]
                if file_name[-3:] == '.py':
                    self.file_coverage[file_name] = {}
                    # Account for 100% format
                    if ((len(data) > 3) and (data[3] == '100%')):
                        self.file_coverage[file_name] = {
                                'statements': data[1],
                                'miss': '0',
                                'cover': data[2],
                                'missing': '',
                        }
                    # Account for 0%-99% format
                    elif (len(data) > 4):
                        self.file_coverage[file_name] = {
                                'statements': data[1],
                                'miss': data[2],
                                'cover': data[3],
                                'missing': data[4],
                        }
        pprint(self.file_coverage)


    def rankTests(self):
        call(['cd', self.test_dir])
        # TODO: iterate over .coverage files, combining & comparing
        # Leverage self.file_coverage
        


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    requiredNamed = parser.add_argument_group('required named arguments')
    requiredNamed.add_argument(
        '--cov-package', dest='cov_package',
       help='Package for which coverage is collected', required=True,
    )
    requiredNamed.add_argument(
        '--test-dir', dest='test_dir',
       help='Directory where tests are located', required=True,
    )

    args = parser.parse_args()
    #ranker = coverageRanking('pyllist', '/Users/kking/SWTestProject/pypy-llist-master/test')
    ranker = coverageRanking(args.cov_package, args.test_dir)
    ranker.parseTests()
    ranker.runTests()
