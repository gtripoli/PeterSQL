import re

from typing import Optional


class StatementExtractor:
    _string_pattern = re.compile(r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"")
    _comment_pattern = re.compile(r"--[^\n]*|/\*.*?\*/", re.DOTALL)

    @staticmethod
    def normalize_separator(
        separator: Optional[str], *, default: str = ";"
    ) -> str:
        raw_separator = (separator or "").strip()
        if not raw_separator:
            return default

        if len(raw_separator) == 1:
            return raw_separator

        if re.fullmatch(r"[A-Za-z0-9_]+", raw_separator):
            return raw_separator

        return default

    @staticmethod
    def _statement_boundaries(text: str, cleaned_text: str, separator: str) -> list[int]:
        boundaries = [0]

        if len(separator) == 1:
            for idx, char in enumerate(cleaned_text):
                if char == separator:
                    boundaries.append(idx + 1)
        else:
            pattern = re.compile(rf"\b{re.escape(separator)}\b", re.IGNORECASE)
            for match in pattern.finditer(cleaned_text):
                boundaries.append(match.end())

        boundaries.append(len(text))
        return boundaries

    @staticmethod
    def _trim_statement(
        statement: str,
        cursor_offset: int,
        separator: str,
    ) -> tuple[str, int]:
        statement_without_separator = statement
        if len(separator) == 1:
            if statement_without_separator.endswith(separator):
                statement_without_separator = statement_without_separator[:-1]
        else:
            separator_pattern = re.compile(
                rf"\b{re.escape(separator)}\b\s*$",
                re.IGNORECASE,
            )
            statement_without_separator = separator_pattern.sub(
                "",
                statement_without_separator,
                count=1,
            )

        if statement_without_separator != statement:
            cursor_offset = min(cursor_offset, len(statement_without_separator))

        statement = statement_without_separator

        leading_whitespace = len(statement) - len(statement.lstrip())
        trimmed_statement = statement.lstrip()
        relative_pos = max(0, cursor_offset - leading_whitespace)
        relative_pos = min(relative_pos, len(trimmed_statement))

        return trimmed_statement, relative_pos
    
    @staticmethod
    def extract_current_statement(
        text: str,
        cursor_pos: int,
        separator: Optional[str] = None,
    ) -> tuple[str, int]:
        effective_separator = StatementExtractor.normalize_separator(separator)
        cleaned_text = StatementExtractor._remove_strings_and_comments(text)

        statement_boundaries = StatementExtractor._statement_boundaries(
            text,
            cleaned_text,
            effective_separator,
        )
        
        for i in range(len(statement_boundaries) - 1):
            start = statement_boundaries[i]
            end = statement_boundaries[i + 1]
            
            if start <= cursor_pos <= end:
                statement = text[start:end]

                cursor_offset = cursor_pos - start
                statement, relative_pos = StatementExtractor._trim_statement(
                    statement,
                    cursor_offset,
                    effective_separator,
                )

                return statement, relative_pos
        
        return text, cursor_pos
    
    @staticmethod
    def extract_all_statements(
        text: str,
        separator: Optional[str] = None,
    ) -> list[tuple[str, int, int]]:
        """Return all statements as (text, start_pos, end_pos) tuples."""
        if not text.strip():
            return []

        effective_separator = StatementExtractor.normalize_separator(separator)
        cleaned = StatementExtractor._remove_strings_and_comments(text)
        boundaries = StatementExtractor._statement_boundaries(
            text,
            cleaned,
            effective_separator,
        )

        results = []
        for i in range(len(boundaries) - 1):
            start, end = boundaries[i], boundaries[i + 1]
            statement = text[start:end]
            if len(effective_separator) == 1:
                if statement.endswith(effective_separator):
                    statement = statement[:-1]
            else:
                statement = re.sub(
                    rf"\b{re.escape(effective_separator)}\b\s*$",
                    "",
                    statement,
                    count=1,
                    flags=re.IGNORECASE,
                )
            statement = statement.strip()
            if statement:
                results.append((statement, start, end))

        return results

    @staticmethod
    def _remove_strings_and_comments(text: str) -> str:
        text = StatementExtractor._string_pattern.sub(lambda m: ' ' * len(m.group(0)), text)
        text = StatementExtractor._comment_pattern.sub(lambda m: ' ' * len(m.group(0)), text)
        return text
