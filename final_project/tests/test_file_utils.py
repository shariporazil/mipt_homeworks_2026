import tempfile
from pathlib import Path
from typing import Any
from app.file_utils import (
    _slurp, expand_refs, chunkify, parse_chunk_cmd, FileProblem,
)


class TestSlurp:

    def test_ok(self) -> None:
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.txt', delete=False, encoding='utf-8'
        ) as f:
            f.write('hello')
            path = f.name
        try:
            assert _slurp(path) == 'hello'
        finally:
            Path(path).unlink()

    def test_not_found(self) -> None:
        import pytest
        with pytest.raises(FileProblem):
            _slurp('/no/such/file.txt')

    def test_too_big(self, monkeypatch: Any) -> None:
        import pytest
        monkeypatch.setattr('app.file_utils._LIMIT', 5)
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.txt', delete=False, encoding='utf-8'
        ) as f:
            f.write('x' * 100)
            path = f.name
        try:
            with pytest.raises(FileProblem):
                _slurp(path)
        finally:
            Path(path).unlink()


class TestExpandRefs:

    def test_no_refs(self) -> None:
        assert expand_refs('просто текст') == 'просто текст'

    def test_with_ref(self, tmp_path: Any) -> None:
        f = tmp_path / 'test.txt'
        f.write_text('содержимое', encoding='utf-8')
        result = expand_refs(f'привет @::{f}:: пока')
        assert 'содержимое' in result

    def test_bad_ref(self) -> None:
        result = expand_refs('@::/no/file::')
        assert 'Ошибка чтения' in result


class TestChunkify:

    def test_paragraphs(self) -> None:
        result = chunkify('a\n\nb\n\nc', 'paragraph', 1)
        assert result == ['a', 'b', 'c']

    def test_paragraphs_grouped(self) -> None:
        result = chunkify('a\n\nb\n\nc\n\nd', 'paragraph', 2)
        assert result == ['a\n\nb', 'c\n\nd']

    def test_length(self) -> None:
        result = chunkify('abcdef', 'len', 2)
        assert result == ['ab', 'cd', 'ef']


class TestParseChunkCmd:

    def test_default(self) -> None:
        assert parse_chunk_cmd('') == ('paragraph', 1, False)

    def test_auto(self) -> None:
        assert parse_chunk_cmd('-y') == ('paragraph', 1, True)

    def test_para(self) -> None:
        assert parse_chunk_cmd('paragraph=3') == ('paragraph', 3, False)

    def test_len(self) -> None:
        assert parse_chunk_cmd('len=100') == ('len', 100, False)

    def test_combined(self) -> None:
        assert parse_chunk_cmd('len=200 -y') == ('len', 200, True)