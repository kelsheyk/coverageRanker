#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, re
from os.path import isfile, join
from subprocess import call
from pprint import pprint

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
                    command = 'py.test --cov=' + self.cov_package + ' ' \
                            + test_file + '::' + test_class + '::' + test
                    call(command.split(' '))
                    # Copy coverage to named data file
                    new_cov_file = '.coverage.' + test_class + '.' + test
                    call(['mv', '.coverage', 'covData/'+new_cov_file])


    def rankTests(self):
        call(['cd', self.test_dir])
        # TODO: iterate over .coverage files, combining & comparing
        


if __name__ == "__main__":
    # TODO: pass in args from CL
    ranker = coverageRanking('pyllist', '/Users/kking/SWTestProject/pypy-llist-master/test')
    ranker.parseTests()
    ranker.runTests()
