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
    file_coverage = {}
    file_line_representations = {}
    num_smoke_tests = 5

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
                print('\n\n\n')
                i =0
                for test in test_list:
                  i+=1
                  if i<20:
                    full_test_name = test_file + '::' + test_class + '::' + test
                    # Run test with coverage
                    # py.test --cov=pyllist test/test_pyllist.py::testdllist::test_init_empty
                    command = 'py.test --cov-report term-missing --cov=' + self.cov_package + ' ' \
                            + full_test_name 
                    cov_report = subprocess.run(command.split(' '), stdout=subprocess.PIPE)
                    self.parseCovReport(full_test_name, cov_report.stdout.decode('utf-8'))
                    # Copy coverage to named data file
                    new_cov_file = '.coverage.' + test_class + '.' + test
                    call(['mv', '.coverage', 'covData/'+new_cov_file])

    def parseMissingLines(self, file_name, string_missing):
        continuous_string_match = re.compile(r'(\d+)-(\d+)')
        individual_line_string_match = re.compile(r'(\d+)')
        line_arr = self.file_line_representations[file_name]
        for missing in string_missing.split(','):
            if re.search(continuous_string_match, missing):
                first = int(re.search(continuous_string_match, missing).group(1))
                last = int(re.search(continuous_string_match, missing).group(2))
                for i in range(first,last):
                    line_arr[i] = False
            elif re.search(individual_line_string_match, missing):
                index = int(re.search(individual_line_string_match, missing).group(1))
                line_arr[index] = False
        return line_arr


    def file_len(self, fname):
        with open(fname) as f:
            i = 1
            for line in enumerate(f):
                i+=1
            return i
    
    # Report Format: ['Name', 'Stmts', 'Miss', 'Cover', 'Missing']
    def parseCovReport(self, test_name, cov_report):
        self.file_coverage[test_name] = {}
        lines = cov_report.split('\n')
        for line in lines:
            # If python file
            data = line.replace(', ', ',').split()
            if len(data):
                file_name = data[0]
                if file_name[-3:] == '.py':
                    self.file_coverage[test_name][file_name] = {}
                    if file_name not in self.file_line_representations:
                        file_lines = self.file_len(file_name)
                        self.file_line_representations[file_name] = [True for i in range(0,file_lines)]
                    # Account for 100% format
                    if ((len(data) > 3) and (data[3] == '100%')):
                        line_coverage = self.parseMissingLines(file_name,'')
                        self.file_coverage[test_name][file_name] = line_coverage
                    # Account for 0%-99% format
                    elif (len(data) > 4):
                        line_coverage = self.parseMissingLines(file_name, data[4])
                        self.file_coverage[test_name][file_name] = line_coverage
        pprint(self.countOverallCovered(self.file_coverage[test_name]))


    def countOverallCovered(self, test_cov_dict):
        covered_count = 0
        for file_name,file_cov in test_cov_dict.items():
            for line in file_cov:
                    if line:
                        covered_count+=1
        #pprint(covered_count)
        return covered_count

    def coverage_merger(self, array1, array2):
        array3 = []
        i = 0
        while(i < len(array1)):
            if array1[i] == True or array2[i] == True:
                array3.append(True)
            else:
                array3.append(False)
            i += 1
        return array3

    def rankTests(self):
        call(['cd', self.test_dir])
        # Leverage self.file_coverage
        # At this point, self.file_coverage has:
        # {test_name: {file_name: [T,T,T,F,F,T,...] }}
        # The array for each file has len = # lines in file
        #       and T=covered, F=missed

        # Start with test that covers most (heuristic)
        base_cov = 0
        for test_name, test_dict in self.file_coverage.items():
            test_cov = self.countOverallCovered(test_dict)
            if test_cov > base_cov:
                pprint(test_name)
                base_cov = test_cov
                base_test = test_name

        # TODO: start with base_test, count non-overlapping coverage for each other test
        # merge test with biggest non-overlapping cov
        # repeat until num_smoke_tests
        current_smoke_merge = {}
        for file_name, file_cov in self.file_coverage[base_test].items():
            current_smoke_merge[file_name] = file_cov
        smoke_tests = [base_test]
        highest_merge_count = self.countOverallCovered(self.file_coverage[base_test])
        for i in range(0,self.num_smoke_tests):
            for test_name, test_dict in self.file_coverage.items():
                if test_name not in smoke_tests:
                    merged_files = {}
                    for file_name,file_cov in test_dict.items():
                        merged_files[file_name] = self.coverage_merger(current_smoke_merge[file_name],file_cov)
                    merge_count = self.countOverallCovered(merged_files)
                    if merge_count >= highest_merge_count:
                        highest_merge = merged_files
                        highest_merge_count = merge_count
                        highest_merge_test = test_name
            #pprint(highest_merge_test)
            #pprint(highest_merge_count)
            smoke_tests.append(highest_merge_test)
            current_smoke_merge = highest_merge
        print('\n\n\n')
        pprint(smoke_tests)
        pprint(highest_merge_count)






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
    ranker = coverageRanking(args.cov_package, args.test_dir)
    ranker.parseTests()
    ranker.runTests()
    #pprint(ranker.file_coverage)
    ranker.rankTests()
