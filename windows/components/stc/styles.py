import wx
import wx.stc

from helpers import wx_colour_to_hex

from windows.components.stc.profiles import SyntaxProfile


def get_palette() -> dict[str, str]:
    background = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
    foreground = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)
    line_number_background = wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DFACE)
    line_number_foreground = wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)
    is_dark = wx.SystemSettings.GetAppearance().IsDark()

    base = {
        "background": background,
        "foreground": foreground,
        "line_number_background": line_number_background,
        "line_number_foreground": line_number_foreground,
    }

    if is_dark:
        return {
            **base,
            "keyword": "#569cd6",
            "string": "#ce9178",
            "comment": "#6a9955",
            "number": "#b5cea8",
            "operator": wx_colour_to_hex(foreground),
            "property": "#9cdcfe",
            "error": "#f44747",
            "uri": "#4ec9b0",
            "reference": "#4ec9b0",
            "document": "#c586c0",
        }

    return {
        **base,
        "keyword": "#0000ff",
        "string": "#990099",
        "comment": "#007f00",
        "number": "#ff6600",
        "operator": "#000000",
        "property": "#0033aa",
        "error": "#cc0000",
        "uri": "#006666",
        "reference": "#006666",
        "document": "#7a1fa2",
    }


def apply_common_style(
    editor: wx.stc.StyledTextCtrl,
    palette: dict[str, str],
    *,
    clear_all: bool = True,
) -> None:
    font = wx.Font(10, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

    if clear_all:
        editor.StyleClearAll()

    editor.StyleSetFont(wx.stc.STC_STYLE_DEFAULT, font)
    editor.StyleSetBackground(wx.stc.STC_STYLE_DEFAULT, palette["background"])
    editor.StyleSetForeground(wx.stc.STC_STYLE_DEFAULT, palette["foreground"])

    line_number_spec = (
        f"back:{wx_colour_to_hex(palette['line_number_background'])},"
        f"fore:{wx_colour_to_hex(palette['line_number_foreground'])}"
    )
    editor.StyleSetSpec(wx.stc.STC_STYLE_LINENUMBER, line_number_spec)
    editor.SetMarginBackground(0, palette["line_number_background"])

    editor.SetCaretForeground(palette["foreground"])
    editor.SetSelBackground(True, wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT))
    editor.SetSelForeground(True, wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT))


def apply_stc_base(editor: wx.stc.StyledTextCtrl) -> None:
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

    editor.SetMarginWidth(1, 0)
    editor.SetMarginWidth(2, 0)


def apply_sql_style(editor: wx.stc.StyledTextCtrl) -> None:
    palette = get_palette()
    editor.SetLexer(wx.stc.STC_LEX_SQL)
    apply_common_style(editor, palette)

    editor.StyleSetSpec(wx.stc.STC_SQL_NUMBER, f"fore:{palette['number']}")

    editor.StyleSetSpec(wx.stc.STC_SQL_COMMENT, f"fore:{palette['comment']},italic")
    editor.StyleSetSpec(wx.stc.STC_SQL_COMMENTLINE, f"fore:{palette['comment']},italic")
    editor.StyleSetSpec(wx.stc.STC_SQL_COMMENTDOC, f"fore:{palette['comment']},italic")

    editor.StyleSetSpec(wx.stc.STC_SQL_WORD, f"fore:{palette['keyword']},bold")

    editor.StyleSetSpec(wx.stc.STC_SQL_CHARACTER, f"fore:{palette['string']}")
    editor.StyleSetSpec(wx.stc.STC_SQL_STRING, f"fore:{palette['string']}")

    editor.StyleSetSpec(wx.stc.STC_SQL_OPERATOR, f"fore:{palette['operator']},bold")

    identifier_color = (
        wx_colour_to_hex(palette["foreground"])
        if palette["operator"] != "#000000"
        else "#333333"
    )
    editor.StyleSetSpec(wx.stc.STC_SQL_IDENTIFIER, f"fore:{identifier_color}")
    editor.StyleSetSpec(wx.stc.STC_SQL_QUOTEDIDENTIFIER, f"fore:{identifier_color}")


def apply_json_style(editor: wx.stc.StyledTextCtrl) -> None:
    palette = get_palette()
    editor.SetLexer(wx.stc.STC_LEX_JSON)
    apply_common_style(editor, palette)

    foreground_hex = wx_colour_to_hex(palette["foreground"])
    editor.StyleSetSpec(wx.stc.STC_JSON_DEFAULT, f"fore:{foreground_hex}")
    editor.StyleSetSpec(wx.stc.STC_JSON_PROPERTYNAME, f"fore:{palette['property']},bold")
    editor.StyleSetSpec(wx.stc.STC_JSON_STRING, f"fore:{palette['string']}")
    editor.StyleSetSpec(wx.stc.STC_JSON_STRINGEOL, f"fore:{palette['string']}")
    editor.StyleSetSpec(wx.stc.STC_JSON_NUMBER, f"fore:{palette['number']}")
    editor.StyleSetSpec(wx.stc.STC_JSON_KEYWORD, f"fore:{palette['keyword']},bold")
    editor.StyleSetSpec(wx.stc.STC_JSON_OPERATOR, f"fore:{palette['operator']},bold")

    editor.StyleSetSpec(wx.stc.STC_JSON_LINECOMMENT, f"fore:{palette['comment']},italic")
    editor.StyleSetSpec(wx.stc.STC_JSON_BLOCKCOMMENT, f"fore:{palette['comment']},italic")

    editor.StyleSetSpec(wx.stc.STC_JSON_ESCAPESEQUENCE, f"fore:{palette['keyword']},bold")

    editor.StyleSetSpec(wx.stc.STC_JSON_URI, f"fore:{palette['uri']},underline")
    editor.StyleSetSpec(wx.stc.STC_JSON_COMPACTIRI, f"fore:{palette['uri']},underline")
    editor.StyleSetSpec(wx.stc.STC_JSON_LDKEYWORD, f"fore:{palette['keyword']},bold")

    editor.StyleSetSpec(wx.stc.STC_JSON_ERROR, f"fore:{palette['error']},bold")


def apply_plain_style(editor: wx.stc.StyledTextCtrl) -> None:
    editor.SetLexer(wx.stc.STC_LEX_NULL)


def apply_yaml_style(editor: wx.stc.StyledTextCtrl) -> None:
    palette = get_palette()
    editor.SetLexer(wx.stc.STC_LEX_YAML)
    apply_common_style(editor, palette)

    foreground_hex = wx_colour_to_hex(palette["foreground"])
    editor.StyleSetSpec(wx.stc.STC_YAML_DEFAULT, f"fore:{foreground_hex}")
    editor.StyleSetSpec(wx.stc.STC_YAML_COMMENT, f"fore:{palette['comment']},italic")
    editor.StyleSetSpec(wx.stc.STC_YAML_IDENTIFIER, f"fore:{palette['property']},bold")
    editor.StyleSetSpec(wx.stc.STC_YAML_KEYWORD, f"fore:{palette['keyword']},bold")
    editor.StyleSetSpec(wx.stc.STC_YAML_NUMBER, f"fore:{palette['number']}")
    editor.StyleSetSpec(wx.stc.STC_YAML_REFERENCE, f"fore:{palette['reference']},underline")
    editor.StyleSetSpec(wx.stc.STC_YAML_TEXT, f"fore:{palette['string']}")
    editor.StyleSetSpec(wx.stc.STC_YAML_DOCUMENT, f"fore:{palette['document']},bold")
    editor.StyleSetSpec(wx.stc.STC_YAML_OPERATOR, f"fore:{palette['operator']},bold")
    editor.StyleSetSpec(wx.stc.STC_YAML_ERROR, f"fore:{palette['error']},bold")


def apply_stc_theme(editor: wx.stc.StyledTextCtrl, syntax_profile: SyntaxProfile) -> None:
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

    editor.SetCaretForeground(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT))
    editor.SetSelBackground(True, wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT))
    editor.SetSelForeground(True, wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT))
