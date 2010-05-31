
import unittest
import doctestplusplus as dtpp

class DocTestPlusPlusTests(unittest.TestCase):
    def setUp(self): pass
    def tearDown(self): pass

    def testCommonPrefixLen_AllNonEmpty(self):
        """
        Test the common prefixes of a few non-empty strings.
        """
        instrings = ["Hello World", "Hell on earth", "Helium Balloons"]
        self.assertEqual(3, dtpp.find_common_prefix_len(instrings))

    def testCommonPrefixLen_AllNonEmptyWithoutCommonPrefixes(self):
        """
        Test the common prefixes of a few non-empty strings without any common prefixes
        """
        instrings = ["Hello World", "Good Bye World", "Sayonara World"]
        self.assertEqual(0, dtpp.find_common_prefix_len(instrings))

    def testCommonPrefixLen_WithSomeCommonPrefixes(self):
        """
        Test the common prefixes of a few strings where only some of them
        match.
        """
        instrings = ["Hello World", "Hell on Earth", "Good Bye World", "Sayonara World"]
        self.assertEqual(0, dtpp.find_common_prefix_len(instrings))

    def testCommonPrefixLen_WithEmptyFewStrings(self):
        """
        Test the common prefixes of a few strings where some of them are
        empty.
        """
        instrings = ["Hello World", "", "", "Hello World"]
        self.assertEqual(0, dtpp.find_common_prefix_len(instrings))

    def testCommentsInFile_EmptyFile(self):
        contents = """ """
        comments = [ g for g in dtpp.comments_in_file(contents)]
        self.assertEqual(0, len(comments))

    def testCommentsInFile_SingleComment(self):
        contents = """ /** Comment 1 */ """
        comments = [ g for g in dtpp.comments_in_file(contents)]
        # should have 1 comment
        self.assertEqual(1, len(comments))

        comment_text, comment_span = comments[0]

        # beginning at offset 1
        self.assertEqual(1, comment_span[0])

        # and value "* Comment 1 "
        self.assertEquals("/** Comment 1 */", comment_text)

    def testCommentsInFile_SingleMultiLineComment(self):
        contents =  \
        """
        /** 
         * First Line
         *
         * Another line here
         */
        """

        comments = [ g for g in dtpp.comments_in_file(contents)]
        # should have 1 comment
        self.assertEqual(1, len(comments))

        comment_text, comment_span = comments[0]

        # beginning at offset 9
        self.assertEqual(9, comment_span[0])

        # and value 
        self.assertEquals(contents.strip(), comment_text)

    def testCommentsInFile_SingleCommentInQuotes(self):
        """
        Comments in quotes are not returned.
        """
        contents =  """ a = "/* no Comment */" """

        comments = [ g for g in dtpp.comments_in_file(contents)]

        # should have 0 comments
        self.assertEqual(0, len(comments))

    def testCommentsInFile_SingleCommentInAndOutOfQuotes(self):
        """
        Comments in quotes are not returned.
        """
        contents =  """ a = "/* not a Comment */" /** A Comment Indeed */ """

        comments = [ g for g in dtpp.comments_in_file(contents)]

        # should have 0 comments
        self.assertEqual(1, len(comments))
        self.assertEqual("/** A Comment Indeed */", comments[0][0])

    def testEvalLineOffsets(self):
        lines = "a\nb\nc\nd"
        offsets = dtpp.evaluate_file_line_offsets(lines, False)
        self.assertEqual([0, 2, 4, 6, 8], offsets)

    def testEvalLineOffsetsWithEmptyLines(self):
        lines = "a\nb\n\n\nc\nd"
        offsets = dtpp.evaluate_file_line_offsets(lines, False)
        self.assertEqual([0, 2, 4, 5, 6, 8, 10], offsets)

    def testEvalLineOffsetsWithAllEmptyLines(self):
        lines = "\n\n\n\n\n"
        offsets = dtpp.evaluate_file_line_offsets(lines, False)
        self.assertEqual([0, 1, 2, 3, 4, 5, 6], offsets)

    #
    # Now the hard stuff - testing for actual test blocks inside a comment
    #
    def testBlocksInComment_CommentWithoutTests(self):
        comment = "/* Boring Text */"
        tests   = [t for t in dtpp.test_blocks_in_comment(comment)]
        self.assertEqual(0, len(tests))

    def testBlocksInComment_CommentWithSingleTest(self):
        comment = """
        /**
         * A Boring Text
         * More Boring test
         *
         * @test(Test1)
         * @endtest
         */
        """
        tests   = [t for t in dtpp.test_blocks_in_comment(comment)]
        self.assertEqual(1, len(tests))
        self.assertEqual("", tests[0].test_body)

if __name__ == '__main__':
    unittest.main()
