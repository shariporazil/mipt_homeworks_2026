from typing import Dict, List, Optional

class History:

    def __init__(
        self,
        system: Optional[str] = None,
        max_msgs: Optional[int] = None,
        max_chars: Optional[int] = None,
    ):
        self._items: List[Dict[str, str]] = []
        self._max_msgs = max_msgs
        self._max_chars = max_chars
        if system:
            self._items.append({'role': 'system', 'content': system})

    def clone(self) -> List[Dict[str, str]]:
        return list(self._items)

    def push(self, role: str, text: str) -> None:
        self._items.append({'role': role, 'content': text})
        self._crop()

    def drop_last(self) -> None:
        if self._items:
            self._items.pop()

    def wipe(self, system: Optional[str] = None) -> None:
        self._items.clear()
        if system:
            self._items.append({'role': 'system', 'content': system})

    def _has_sys(self) -> bool:
        return len(self._items) > 0 and self._items[0]['role'] == 'system'

    def _start(self) -> int:
        return 1 if self._has_sys() else 0

    def _crop(self) -> None:
        s = self._start()
        if s >= len(self._items):
            return

        if self._max_msgs is not None:
            cap = self._max_msgs + (1 if self._has_sys() else 0)
            while len(self._items) > cap and len(self._items) > s:
                self._items.pop(s)

        if self._max_chars is not None:
            while len(self._items) > s:
                total = sum(len(m['content']) for m in self._items)
                if total <= self._max_chars:
                    break
                if len(self._items) - s == 1:
                    cut = total - self._max_chars
                    self._items[s]['content'] = self._items[s]['content'][cut:]
                    break
                self._items.pop(s)
                