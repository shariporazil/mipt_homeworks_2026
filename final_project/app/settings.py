import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv

def _read_yaml() -> Dict[str, Any]:
    p = Path('config.yaml')
    if not p.is_file():
        return {}
    raw = p.read_text(encoding='utf-8')
    data = yaml.safe_load(raw)
    return data if isinstance(data, dict) else {}

def _env_or_yaml(env_key: str, yaml_key: str, data: Dict[str, Any]) -> Optional[str]:
    return os.environ.get(env_key) or data.get(yaml_key)

def _fail(msg: str) -> None:
    print(msg)
    sys.exit(1)

def _to_int(raw: Optional[str], label: str) -> Optional[int]:
    if raw is None or raw == '':
        return None
    try:
        n = int(raw)
    except ValueError:
        _fail(f'{label} должен быть целым числом')
        return None
    if n < 1:
        _fail(f'{label} должен быть >= 1')
    return n

def _to_float(raw: Optional[str], lo: float, hi: float, label: str) -> float:
    if raw is None:
        return 0.7
    try:
        v = float(raw)
    except ValueError:
        _fail(f'{label} должен быть числом')
        return 0.7
    if not (lo <= v <= hi):
        _fail(f'{label} должен быть от {lo} до {hi}')
    return v

def load() -> Dict[str, Any]:
    load_dotenv()
    yaml_data = _read_yaml()

    host_raw = _env_or_yaml('API_HOST', 'api_host', yaml_data)
    if not host_raw:
        _fail('API_HOST не задан — проверьте config.yaml или .env')
    assert host_raw is not None
    host: str = host_raw.rstrip('/')

    key: str = _env_or_yaml('API_KEY', 'api_key', yaml_data) or 'ollama'
    model: str = _env_or_yaml('MODEL_NAME', 'model_name', yaml_data) or 'gemma3:270m'

    temp_raw = _env_or_yaml('TEMPERATURE', 'temperature', yaml_data)
    temperature: float = _to_float(temp_raw, 0.0, 1.0, 'TEMPERATURE')

    msg_raw = _env_or_yaml('LIMIT_MESSAGE', 'limit_message', yaml_data)
    limit_message = _to_int(msg_raw, 'LIMIT_MESSAGE')

    sym_raw = _env_or_yaml('LIMIT_CHARS', 'limit_chars', yaml_data)
    limit_chars = _to_int(sym_raw, 'LIMIT_CHARS')

    system_prompt = yaml_data.get('system_prompt')

    return {
        'api_host': host,
        'api_key': key,
        'model_name': model,
        'temperature': temperature,
        'limit_message': limit_message,
        'limit_chars': limit_chars,
        'system_prompt': system_prompt,
    }
