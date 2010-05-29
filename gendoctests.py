
import re, sys, os

quoted_string_re    = r"""   "[^"]*(?!\\)"   |  '[^']*(?!\\)'    """
quote_or_comment    = re.compile(r"""   "[^"]*"   |  '[^']*'  |   \/\/[^\r\n]*$   | \/\*.*?\*\/  """, re.X | re.S)

# 
# Matches "@test(TestName" without the closing bracket.
# This will return the name of the test.
#
attest_and_testname_re  = re.compile(r""" @test \s* \( \s* (?P<TestName>\w+) \s*""", re.S | re.X)

# 
# Now we match an argument at the start of the string and return the
# argname and argvalue or a ")" signalling the end of the arguments
#
arg_name_re             = r"\s* (?P<ArgName>\w+) \s* "
arg_name_value_re       = re.compile(r"""\s* , """ + arg_name_re + " = \s* (?P<ArgValue>""" + quoted_string_re + " ) | \s* \) [ \t\v\f]* [\n\r]* """, re.S | re.X)

#
# Find the @endtest that is not preceeded by a "@"
#
endtest_re              = re.compile(""" (?<!@)@endtest """, re.S | re.X)

class DocTest(object):
    def __init__(self, name, offset, args, body, body_offset):
        self.test_name          = name
        self.test_offset        = offset
        self.test_args          = args
        self.test_body          = body
        self.test_body_offset   = body_offset

    def describe(self):
        print "Test Name: %s @ %d" % (self.test_name, self.test_offset)
        print "Test Args: ", self.test_args
        print "Test Body @ %d: " % (self.test_body_offset)
        print self.test_body

def find_common_prefix(strings):
    """
    Given a list of strings, finds the common prefix in all of them.
    So 
    apple
    applet
    application

    would return "app"
    """
    prefix          = ""
    curr_index      = -1
    num_strings     = len(strings)
    string_lengths  = [len(s) for s in strings]
    while True:
        curr_index  += 1
        ch_in_si    = None
        for si in xrange(0, num_strings):
            if curr_index >= string_lengths[si]:
                return prefix
            else:
                if si == 0:
                    ch_in_si = strings[0][curr_index]
                elif strings[si][curr_index] != ch_in_si:
                    return prefix
        prefix += strings[0][curr_index]

def comments_in_file(file_contents):
    """
    Given file contents parses it and yields the multiline comments from it
    one block at a time.

    The scanner is very simply.  We do not really care about non comments.
    Only issue we want to ignore false comment starts - ie the comment
    string "/*" beginning inside double or single quotes.
    Also to keep it simple we do not care of single line comments (ie //)
    """
    for block in quote_or_comment.finditer(file_contents):
        if block.group().startswith("/*"):
            yield block.group(), block.span()

def test_blocks_in_comment(comment):
    """
    Given a block of comment, yields each block of test within it one at a time.
    Rules are simple:
        1. Test begins with @test and ends with @endtest
        2. To allow a @endtest within the test itself prefix it with "@".
        3. @test is followed by parameters enclosed in parantheses.  The
        first parameter MUST be the name of the test case.  So far the
        following parameters are allowed:
            suite   -   The Suite in which the tests will be generated.
            fixture -   The fixture to which the test belongs.
    """

    curr_offset     = 0
    comment_left    = comment

    test_match      = attest_and_testname_re.search(comment_left)
    while test_match:
        test_name   = test_match.group(1)
        test_offset = curr_offset + test_match.start()

        # strip away the @test(<TestName> * bit
        comment_left    = comment_left[test_match.end():]

        # update current offset to reflect "chomped away" bits
        curr_offset     += test_match.end()

        test_args = {}

        # now match the arguments at the start of the list
        # if none matched then we should have a ")"
        while True:
            argmatch = arg_name_value_re.match(comment_left)
            if not argmatch:
                print "Comment Left: |", comment_left
                raise DTException("Missing argument or closing parenthesis in @test", curr_offfset)

            # chomp away the arg
            comment_left = comment_left[argmatch.end():]
            curr_offset += argmatch.end()
        
            arg_name, arg_value = argmatch.groups()
            if not (arg_name and arg_value):
                # we have reached the end
                break

            # otherwise read the argument and store it
            test_args[arg_name] = arg_value[1:-1]       # strip quotes

        # ok now read the test contents - this is anythign ending with @endtest
        etmatch = endtest_re.search(comment_left)
        if not etmatch:
            raise DTException("Did not find a terminating @endtest", curr_offfset)

        test_body_offset = curr_offset
        test_body = comment_left[:etmatch.start()]

        comment_left = comment_left[etmatch.end():]
        curr_offset += etmatch.end()

        yield DocTest(test_name, test_offset, test_args, test_body, test_body_offset)

        # get the next text match
        test_match  = attest_and_testname_re.search(comment_left)

def tests_in_file(filename):
    """
    Given a file, yields all the test cases one by one along with the
    offset in the file the comment falls in.
    """
    comments = comments_in_file(open(filename).read())
    for comment, comment_span in comments:
        testblocks = test_blocks_in_comment(comment)
        for testblock in testblocks:
            yield testblock, comment_span

def print_tests_in_file(file):
    """
    Helper for debug printing the test cases in the files.
    """
    for test, comment_span in tests_in_file(file):
        print "Comment Span: ", comment_span
        # print comment
        test.describe()

class DocTestGenerator(object):
    def __init__(self, folder = "", prefix = "", suffix = "_test", ext = ""):
        self.output_folder      = folder
        self.output_file_prefix = prefix
        self.output_file_suffix = suffix
        self.output_file_ext    = ext

    def evaluate_output_file(self, infile, create_output_folder = False):
        """
        Evaluate the output file path based on the input file.
        """
        fullpath, extension = os.path.splitext(infile)
        dirname, basename = os.path.dirname(fullpath), os.path.basename(fullpath)
        if self.output_file_ext:
            extension = self.output_file_ext
            if not extension.startswith("."):
                extension = "." + extension

        output_folder = os.path.abspath(self.output_folder + dirname)
        if output_folder:
            if create_output_folder:
                if not os.path.isdir(output_folder):
                    print "Creating Output Directory: ", output_folder
                    os.makedirs(output_folder)

            return "%s/%s%s%s%s" % (output_folder,
                                    self.output_file_prefix,
                                    basename,
                                    self.output_file_suffix,
                                    extension)
        else:
            return "%s%s%s%s" % (self.output_file_prefix,
                                 basename,
                                 self.output_file_suffix,
                                 extension)

    def evaluate_file_line_offsets(self, file):
        file_lines      = open(file).read().split("\n")
        line_offsets    = [0]
        for line in file_lines:
            line_offsets.append(line_offsets[-1] + len(line))
        return line_offsets

    def evaluate_line_number(self, line_offsets, file_offset):
        num_lines = len(line_offsets)
        for i in xrange(0, num_lines):
            if file_offset < line_offsets[i]:
                return i - 1
        return num_lines - 1

    def generate_test_cases(self, file):
        """
        Given a file, generates an output file with all the test cases in it.
        """
        output_file = self.evaluate_output_file(file, True)
        print "Output File: ", output_file

        assert output_file != file, "Input and Output files are the same"

        outfile = open(output_file, "w")

        # evaluate the offsets within the file of each line so we can
        # calculate which line a particular line falls in
        line_offsets = self.evaluate_file_line_offsets(file)

        indent = 0

        def writeln(line):
            print "%s%s" % (indent * "    ", line)
            outfile.write("%s%s\n" % (indent * "    ", line))

        for test, comment_span in tests_in_file(file):
            test_suite      = test.test_args.get("suite", None)
            test_fixture    = test.test_args.get("fixture", None)

            if test_suite:
                writeln("SUITE(%s)" % test_suite)
                writeln("{")
                indent += 1

            if test_fixture:
                writeln("TEST_FIXTURE(%s, %s)" % (test_fixture, test.test_name))
            else:
                writeln("TEST(%s)" % (test.test_name))
            writeln("{")

            # take care of the actual test body now
            indent += 1
            test_lines = test.test_body.split("\n")
            common_prefix = find_common_prefix(test_lines)
            common_prefix_len = len(common_prefix)

            line_number = self.evaluate_line_number(line_offsets, comment_span[0] + test.test_offset)
            writeln('#line %d "%s"' % (line_number, file))
            for line in test_lines: writeln(line[common_prefix_len:])

            indent -= 1

            # close the TEST/TEST_FIXTURE block
            writeln("}")

            # close the SUITE block if any
            if test_suite:
                indent -= 1
                writeln("}")

            writeln("")     # and an empty line after test cases

        outfile.close()

if __name__ == "__main__":
    from optparse import OptionParser
    optparser = OptionParser(usage = "%prog [options] <files>",
                             version = "%prog 0.1")
    optparser.add_option("-o", "--outfolder", dest = "output_folder", default="",
                         help = "Output folder where test cases are written to.",
                         metavar = "OUTPUT_FOLDER")
    optparser.add_option("-p", "--prefix", dest = "output_file_prefix", default="",
                         help = "Prefix of the generated output files (default - none).",
                         metavar = "OUTPUT_FILE_PREFIX")
    optparser.add_option("-s", "--suffix", dest = "output_file_suffix", default="_tests",
                         help = "Suffix of the generated output files (default - _tests).",
                         metavar = "OUTPUT_FILE_SUFFIX")
    optparser.add_option("-e", "--extension", dest = "output_file_extension", default="",
                         help = "Extension of the generated output files.",
                         metavar = "OUTPUT_FILE_EXT")


    (options, args) = optparser.parse_args()
    # print "Options: ", options
    # print "Args: ", args

    if not args:
        print >> sys.stderr, "Please enter files to generate tests cases for."
        optparser.print_help()

    docgen = DocTestGenerator(options.output_folder,
                              options.output_file_prefix,
                              options.output_file_suffix,
                              options.output_file_extension)
    # process the leftover files
    for arg in args:
        print "Processing File: ", arg
        doc.generate_tests_cases(arg)

