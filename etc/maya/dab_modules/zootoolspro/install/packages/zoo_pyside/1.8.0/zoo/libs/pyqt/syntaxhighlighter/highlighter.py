from Qt import QtGui, QtCore
from zoo.libs.utils import filesystem


def formatColor(color, style=None):
    """Return a QtGui.QTextCharFormat with the given attributes.
    :param color: float3 rgb
    :type color: tuple
    :param style: the style name eg. 'bold'
    :type style: str or None
    """
    style = style or ""
    _color = QtGui.QColor(*color)
    _format = QtGui.QTextCharFormat()
    _format.setForeground(_color)
    if "bold" in style:
        _format.setFontWeight(QtGui.QFont.Bold)
    if "italic" in style:
        _format.setFontItalic(True)

    return _format


def highlighterFromJson(filePath, document):
    """Generate's a python syntaxHighlighter from a json file containing the syntax and color information

    :param filePath: Absolute path to the json file
    :type filePath: str
    :param document: The Document instance to apply to
    :type document: :class:`QtGui.QTextDocument`
    :rtype: :class:`PythonHighlighter`
    """
    if not filePath:
        return
    syntaxData = filesystem.loadJson(filePath)
    return PythonHighlighter(document, syntaxData)


class PythonHighlighter(QtGui.QSyntaxHighlighter):
    """Syntax highlighter for the Python language.
    """

    def __init__(self, document, styles):
        """
        :param document:
        :type document: the textEdit document
        :param styles: The style dict
        :type styles: dict
        """
        QtGui.QSyntaxHighlighter.__init__(self, document)

        colors = styles["colors"]
        syntax = styles["syntax"]
        self.tri_single = (QtCore.QRegExp("'''"), 1, colors['string'])
        self.tri_double = (QtCore.QRegExp('"""'), 2, colors['string'])

        rules = [

            # 'self'
            (r'\bself\b', 0, colors['self']),

            # Double-quoted string, possibly containing escape sequences
            (r'"[^"\\]*(\\.[^"\\]*)*"', 0, colors['string']),
            # Single-quoted string, possibly containing escape sequences
            (r"'[^'\\]*(\\.[^'\\]*)*'", 0, colors['string']),

            # 'def' followed by an identifier
            (r'\bdef\b\s*(\w+)', 1, colors['methods']),
            # 'class' followed by an identifier
            (r'\bclass\b\s*(\w+)', 1, colors['defclass']),

            # From '#' until a newline
            (r'#[^\n]*', 0, colors['comment']),
            (r"\\b[A-Za-z0-9_]+(?=\\()", 0, colors['methods']),
            # Numeric literals
            (r'\b[+-]?[0-9]+[lL]?\b', 0, colors['numbers']),
            (r'\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b', 0, colors['numbers']),
            (r'\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b', 0, colors['numbers']),
        ]
        # Keyword, operator, and brace rules
        rules += [(r'\b%s\b' % w, 0, colors['keyword']) for w in syntax["keywords"]]
        rules += [(r'\b%s\b' % w, 0, colors['preprocessor']) for w in syntax["preprocessors"]]
        rules += [(r'\b%s\b' % w, 0, colors['special']) for w in syntax["specials"]]
        rules += [(r'%s' % o, 0, colors['operator']) for o in syntax["operators"]]
        rules += [(r'%s' % b, 0, colors['brace']) for b in syntax["braces"]]

        # Build a QtCore.QRegExp for each pattern
        self.rules = [(QtCore.QRegExp(pat), index, fmt)
                      for (pat, index, fmt) in rules]

    def highlightBlock(self, text):
        """Apply syntax highlighting to the given block of text.
        """
        # Do other syntax formatting
        for expression, nth, f in self.rules:
            index = expression.indexIn(text, 0)
            if len(f) > 1:
                f = formatColor(f[0], f[1])
            else:
                f = formatColor(f[0])
            while index >= 0:
                # We actually want the index of the nth match
                index = expression.pos(nth)
                length = expression.cap(nth)
                length = len(length)
                self.setFormat(index, length, f)
                index = expression.indexIn(text, index + length)

        self.setCurrentBlockState(0)

        color = QtGui.QColor(*self.tri_single[2][0])
        in_multiline = self.match_multiline(text, self.tri_single[0], self.tri_single[1], color)
        if not in_multiline:
            self.match_multiline(text, self.tri_double[0], self.tri_double[1], color)

    def match_multiline(self, text, delimiter, in_state, style):
        """Do highlighting of multi-line strings. ``delimiter`` should be a
        ``QtCore.QRegExp`` for triple-single-quotes or triple-double-quotes, and
        ``in_state`` should be a unique integer to represent the corresponding
        state changes when inside those strings. Returns True if we're still
        inside a multi-line string when this function is finished.
        """
        # If inside triple-single quotes, start at 0
        if self.previousBlockState() == in_state:
            start = 0
            add = 0
        # Otherwise, look for the delimiter on this line
        else:
            start = delimiter.indexIn(text)
            # Move past this match
            add = delimiter.matchedLength()

        # As long as there's a delimiter match on this line...
        while start >= 0:
            # Look for the ending delimiter
            end = delimiter.indexIn(text, start + add)
            # Ending delimiter on this line?
            if end >= add:
                length = end - start + add + delimiter.matchedLength()
                self.setCurrentBlockState(0)
            # No; multi-line string
            else:
                self.setCurrentBlockState(in_state)
                length = len(text) - start + add
            # Apply formatting
            self.setFormat(start, length, style)
            # Look for the next match
            start = delimiter.indexIn(text, start + length)

        # Return True if still inside a multi-line string, False otherwise
        if self.currentBlockState() == in_state:
            return True
        return False