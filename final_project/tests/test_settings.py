from typing import Any
from app.settings import _to_int, _to_float, load


class TestToInt:

    def test_none(self) -> None:
        assert _to_int(None, 'X') is None

    def test_empty(self) -> None:
        assert _to_int('', 'X') is None

    def test_valid(self) -> None:
        assert _to_int('42', 'X') == 42

    def test_zero_fails(self) -> None:
        import pytest
        with pytest.raises(SystemExit):
            _to_int('0', 'X')

    def test_negative_fails(self) -> None:
        import pytest
        with pytest.raises(SystemExit):
            _to_int('-5', 'X')


class TestToFloat:

    def test_none_default(self) -> None:
        assert _to_float(None, 0.0, 1.0, 'X') == 0.7

    def test_valid(self) -> None:
        assert _to_float('0.3', 0.0, 1.0, 'X') == 0.3

    def test_out_of_range(self) -> None:
        import pytest
        with pytest.raises(SystemExit):
            _to_float('1.5', 0.0, 1.0, 'X')


class TestLoad:

    def test_no_host_fails(self, monkeypatch: Any) -> None:
        monkeypatch.delenv('API_HOST', raising=False)
        monkeypatch.setattr('app.settings.Path.is_file', lambda self: False)
        import pytest
        with pytest.raises(SystemExit):
            load()

    def test_env_overrides_yaml(self, monkeypatch: Any, tmp_path: Any) -> None:
        yaml_file = tmp_path / 'config.yaml'
        content = 'api_host: http://yaml-host:11434\nmodel_name: yaml-model'
        yaml_file.write_text(content, encoding='utf-8')
        monkeypatch.setenv('API_HOST', 'http://env-host:11434')
        monkeypatch.setenv('MODEL_NAME', 'env-model')

        def fake_read_text(self: Any, encoding: Any = None) -> str:
            return content

        monkeypatch.setattr('app.settings.Path.is_file', lambda self: True)
        monkeypatch.setattr('app.settings.Path.read_text', fake_read_text)
        cfg = load()
        assert cfg['api_host'] == 'http://env-host:11434'
        assert cfg['model_name'] == 'env-model'