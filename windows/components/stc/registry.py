from typing import Optional, Sequence

from windows.components.stc.profiles import SyntaxProfile


class SyntaxRegistry:
    def __init__(self, profiles: Sequence[SyntaxProfile]) -> None:
        self._profiles: list[SyntaxProfile] = list(profiles)
        self._by_id: dict[str, SyntaxProfile] = {profile.id: profile for profile in self._profiles}
        self._by_label: dict[str, SyntaxProfile] = {profile.label: profile for profile in self._profiles}

    def all(self) -> list[SyntaxProfile]:
        return list(self._profiles)

    def by_label(self, label: str) -> SyntaxProfile:
        return self._by_label[label]

    def get(self, syntax_id: str) -> SyntaxProfile:
        return self._by_id[syntax_id]

    def labels(self) -> list[str]:
        return [profile.label for profile in self._profiles]

    def select(
        self,
        *,
        label: Optional[str] = None,
        syntax_id: Optional[str] = None,
    ) -> SyntaxProfile:
        if syntax_id is not None:
            return self._by_id[syntax_id]
        if label is not None:
            return self._by_label[label]
        raise ValueError("Either syntax_id or label must be provided")
