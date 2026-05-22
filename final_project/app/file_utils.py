import re
from pathlib import Path
from typing import List, Tuple

_LIMIT = 5 * 1024 * 1024
_MARKER = re.compile(r'@::(.+?)::')

class FileProblem(Exception):
    pass

def _slurp(path: str) -> str:
    p = Path(path)
    if not p.exists():
        raise FileProblem(f'Нет файла: {path}')
    if not p.is_file():
        raise FileProblem(f'Не файл: {path}')
    if p.stat().st_size > _LIMIT:
        mb = p.stat().st_size / (1024 * 1024)
        raise FileProblem(f'Файл {mb:.1f} МБ — больше 5 МБ: {path}')
    try:
        return p.read_text(encoding='utf-8')
    except UnicodeDecodeError as err:
        raise FileProblem(f'Не текст (UTF-8): {path}') from err

def expand_refs(text: str) -> str:
    hits = _MARKER.findall(text)
    out = text
    for fp in hits:
        tag = f'@::{fp}::'
        try:
            body = _slurp(fp)
            out = out.replace(tag, '')
            out += f'\n\n[Файл {fp}]:\n{body}'
        except FileProblem as e:
            print(f'\n[!] {e}')
            out = out.replace(tag, f'[Ошибка чтения {fp}]')
    return out.strip()

def _by_paras(content: str, n: int) -> List[str]:
    paras = [p.strip() for p in content.split('\n') if p.strip()]
    chunks: List[str] = []
    for i in range(0, len(paras), n):
        chunks.append('\n\n'.join(paras[i:i + n]))
    return chunks

def _by_len(content: str, n: int) -> List[str]:
    return [content[i:i + n] for i in range(0, len(content), n)]

def chunkify(content: str, mode: str, val: int) -> List[str]:
    if mode == 'len':
        return _by_len(content, val)
    return _by_paras(content, val)

def parse_chunk_cmd(raw: str) -> Tuple[str, int, bool]:
    mode = 'paragraph'
    val = 1
    auto = False
    for tok in raw.strip().split():
        if tok == '-y':
            auto = True
        elif tok.startswith('paragraph='):
            try:
                val = int(tok.split('=')[1])
                mode = 'paragraph'
            except ValueError:
                pass
        elif tok.startswith('len='):
            try:
                val = int(tok.split('=')[1])
                mode = 'len'
            except ValueError:
                pass
    return mode, val, auto
