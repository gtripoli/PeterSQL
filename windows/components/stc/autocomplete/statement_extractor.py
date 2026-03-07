import re

from typing import Optional


class StatementExtractor:
    _string_pattern = re.compile(r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"")
    _comment_pattern = re.compile(r"--[^\n]*|/\*.*?\*/", re.DOTALL)
    
    @staticmethod
    def extract_current_statement(text: str, cursor_pos: int) -> tuple[str, int]:
        cleaned_text = StatementExtractor._remove_strings_and_comments(text)
        
        statement_boundaries = [0]
        for i, char in enumerate(cleaned_text):
            if char == ';':
                statement_boundaries.append(i + 1)
        statement_boundaries.append(len(text))
        
        for i in range(len(statement_boundaries) - 1):
            start = statement_boundaries[i]
            end = statement_boundaries[i + 1]
            
            if start <= cursor_pos <= end:
                statement = text[start:end]
                
                if statement.endswith(';'):
                    statement = statement[:-1]
                
                statement = statement.lstrip()
                
                relative_pos = cursor_pos - start
                if start > 0:
                    leading_whitespace = len(text[start:]) - len(text[start:].lstrip())
                    relative_pos = cursor_pos - start - leading_whitespace
                
                return statement, relative_pos
        
        return text, cursor_pos
    
    @staticmethod
    def _remove_strings_and_comments(text: str) -> str:
        text = StatementExtractor._string_pattern.sub(lambda m: ' ' * len(m.group(0)), text)
        text = StatementExtractor._comment_pattern.sub(lambda m: ' ' * len(m.group(0)), text)
        return text
