from colored_traceback import Colorizer
from JumpScale import j

class LoggingColorizer(Colorizer):

    def colorize_traceback(self, type, value, tb):
        import traceback
        import pygments.lexers
        tb_text = "".join(traceback.format_exception(type, value, tb))
        lexer = pygments.lexers.get_lexer_by_name("pytb", stripall=True)
        tb_colored = pygments.highlight(tb_text, lexer, self.formatter)
        return tb_colored
