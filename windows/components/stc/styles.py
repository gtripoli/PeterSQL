import wx
import wx.stc

from helpers import wx_colour_to_hex
from windows.components.stc.syntax import SyntaxProfile


def get_palette():
    bg = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
    fg = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)
    ln_bg = wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DFACE)
    ln_fg = wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)
    is_dark = wx.SystemSettings.GetAppearance().IsDark()

    if is_dark:
        return {
            "bg": bg, "fg": fg, "ln_bg": ln_bg, "ln_fg": ln_fg,
            "keyword": "#569cd6",
            "string": "#ce9178",
            "comment": "#6a9955",
            "number": "#b5cea8",
            "operator": wx_colour_to_hex(fg),
            # extra
            "prop": "#9cdcfe",
            "error": "#f44747",
            "uri": "#4ec9b0",
            "ref": "#4ec9b0",
            "doc": "#c586c0",
        }
    else:
        return {
            "bg": bg, "fg": fg, "ln_bg": ln_bg, "ln_fg": ln_fg,
            "keyword": "#0000ff",
            "string": "#990099",
            "comment": "#007f00",
            "number": "#ff6600",
            "operator": "#000000",
            # extra
            "prop": "#0033aa",
            "error": "#cc0000",
            "uri": "#006666",
            "ref": "#006666",
            "doc": "#7a1fa2",
        }


def apply_common_style(editor: wx.stc.StyledTextCtrl, pal, *, clear_all=True):
    font = wx.Font(10, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

    if clear_all:
        editor.StyleClearAll()

    editor.StyleSetFont(wx.stc.STC_STYLE_DEFAULT, font)
    editor.StyleSetBackground(wx.stc.STC_STYLE_DEFAULT, pal["bg"])
    editor.StyleSetForeground(wx.stc.STC_STYLE_DEFAULT, pal["fg"])

    # line numbers
    editor.StyleSetSpec(wx.stc.STC_STYLE_LINENUMBER, f"back:{wx_colour_to_hex(pal['ln_bg'])},fore:{wx_colour_to_hex(pal['ln_fg'])}")
    editor.SetMarginBackground(0, pal["ln_bg"])

    # caret + selection
    editor.SetCaretForeground(pal["fg"])
    editor.SetSelBackground(True, wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT))
    editor.SetSelForeground(True, wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT))


def apply_stc_base(editor: wx.stc.StyledTextCtrl):
    editor.SetUseTabs(False)
    editor.SetTabWidth(4)
    editor.SetIndent(4)
    editor.SetTabIndents(True)
    editor.SetBackSpaceUnIndents(True)

    editor.SetViewEOL(False)
    editor.SetViewWhiteSpace(False)
    editor.SetIndentationGuides(True)
    editor.SetWrapMode(wx.stc.STC_WRAP_NONE)

    editor.SetMarginType(0, wx.stc.STC_MARGIN_NUMBER)
    editor.SetMarginWidth(0, editor.TextWidth(wx.stc.STC_STYLE_LINENUMBER, "_99999"))

    # niente folding nel dialog
    editor.SetMarginWidth(1, 0)
    editor.SetMarginWidth(2, 0)


def apply_sql_style(editor: wx.stc.StyledTextCtrl):
    pal = get_palette()
    editor.SetLexer(wx.stc.STC_LEX_SQL)
    apply_common_style(editor, pal)

    editor.StyleSetSpec(wx.stc.STC_SQL_NUMBER, f"fore:{pal['number']}")

    editor.StyleSetSpec(wx.stc.STC_SQL_COMMENT, f"fore:{pal['comment']},italic")
    editor.StyleSetSpec(wx.stc.STC_SQL_COMMENTLINE, f"fore:{pal['comment']},italic")
    editor.StyleSetSpec(wx.stc.STC_SQL_COMMENTDOC, f"fore:{pal['comment']},italic")

    editor.StyleSetSpec(wx.stc.STC_SQL_WORD, f"fore:{pal['keyword']},bold")

    editor.StyleSetSpec(wx.stc.STC_SQL_CHARACTER, f"fore:{pal['string']}")
    editor.StyleSetSpec(wx.stc.STC_SQL_STRING, f"fore:{pal['string']}")

    editor.StyleSetSpec(wx.stc.STC_SQL_OPERATOR, f"fore:{pal['operator']},bold")

    ident = wx_colour_to_hex(pal["fg"]) if pal["operator"] != "#000000" else "#333333"
    editor.StyleSetSpec(wx.stc.STC_SQL_IDENTIFIER, f"fore:{ident}")
    editor.StyleSetSpec(wx.stc.STC_SQL_QUOTEDIDENTIFIER, f"fore:{ident}")


def apply_json_style(editor: wx.stc.StyledTextCtrl):
    pal = get_palette()
    editor.SetLexer(wx.stc.STC_LEX_JSON)
    apply_common_style(editor, pal)

    editor.StyleSetSpec(wx.stc.STC_JSON_DEFAULT, f"fore:{wx_colour_to_hex(pal['fg'])}")
    editor.StyleSetSpec(wx.stc.STC_JSON_PROPERTYNAME, f"fore:{pal['prop']},bold")
    editor.StyleSetSpec(wx.stc.STC_JSON_STRING, f"fore:{pal['string']}")
    editor.StyleSetSpec(wx.stc.STC_JSON_STRINGEOL, f"fore:{pal['string']}")
    editor.StyleSetSpec(wx.stc.STC_JSON_NUMBER, f"fore:{pal['number']}")
    editor.StyleSetSpec(wx.stc.STC_JSON_KEYWORD, f"fore:{pal['keyword']},bold")
    editor.StyleSetSpec(wx.stc.STC_JSON_OPERATOR, f"fore:{pal['operator']},bold")

    editor.StyleSetSpec(wx.stc.STC_JSON_LINECOMMENT, f"fore:{pal['comment']},italic")
    editor.StyleSetSpec(wx.stc.STC_JSON_BLOCKCOMMENT, f"fore:{pal['comment']},italic")

    editor.StyleSetSpec(wx.stc.STC_JSON_ESCAPESEQUENCE, f"fore:{pal['keyword']},bold")

    editor.StyleSetSpec(wx.stc.STC_JSON_URI, f"fore:{pal['uri']},underline")
    editor.StyleSetSpec(wx.stc.STC_JSON_COMPACTIRI, f"fore:{pal['uri']},underline")
    editor.StyleSetSpec(wx.stc.STC_JSON_LDKEYWORD, f"fore:{pal['keyword']},bold")

    editor.StyleSetSpec(wx.stc.STC_JSON_ERROR, f"fore:{pal['error']},bold")


def apply_plain_style(editor: wx.stc.StyledTextCtrl):
    editor.SetLexer(wx.stc.STC_LEX_NULL)


def apply_yaml_style(editor: wx.stc.StyledTextCtrl):
    pal = get_palette()
    editor.SetLexer(wx.stc.STC_LEX_YAML)
    apply_common_style(editor, pal)

    editor.StyleSetSpec(wx.stc.STC_YAML_DEFAULT, f"fore:{wx_colour_to_hex(pal['fg'])}")
    editor.StyleSetSpec(wx.stc.STC_YAML_COMMENT, f"fore:{pal['comment']},italic")
    editor.StyleSetSpec(wx.stc.STC_YAML_IDENTIFIER, f"fore:{pal['prop']},bold")  # keys
    editor.StyleSetSpec(wx.stc.STC_YAML_KEYWORD, f"fore:{pal['keyword']},bold")
    editor.StyleSetSpec(wx.stc.STC_YAML_NUMBER, f"fore:{pal['number']}")
    editor.StyleSetSpec(wx.stc.STC_YAML_REFERENCE, f"fore:{pal['ref']},underline")
    editor.StyleSetSpec(wx.stc.STC_YAML_TEXT, f"fore:{pal['string']}")
    editor.StyleSetSpec(wx.stc.STC_YAML_DOCUMENT, f"fore:{pal['doc']},bold")
    editor.StyleSetSpec(wx.stc.STC_YAML_OPERATOR, f"fore:{pal['operator']},bold")
    editor.StyleSetSpec(wx.stc.STC_YAML_ERROR, f"fore:{pal['error']},bold")


def apply_stc_theme(editor: wx.stc.StyledTextCtrl, syntax_profile: SyntaxProfile):
    apply_stc_base(editor)

    editor.StyleClearAll()

    if syntax_profile.id == "sql":
        apply_sql_style(editor)
    elif syntax_profile.id == "json":
        apply_json_style(editor)
    elif syntax_profile.id == "yaml":
        apply_yaml_style(editor)
    else:
        apply_plain_style(editor)

    # caret + selection (OS colors)
    editor.SetCaretForeground(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT))
    editor.SetSelBackground(True, wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT))
    editor.SetSelForeground(True, wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT))
