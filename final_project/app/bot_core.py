import os
from typing import Any
from openai import OpenAI

from app.settings import load
from app.message_history import History
from app.file_utils import expand_refs, _slurp, chunkify, parse_chunk_cmd, FileProblem

class ChatBot:

    def __init__(self) -> None:
        cfg = load()
        self._cfg = cfg
        self._hist = History(
            system=cfg.get('system_prompt'),
            max_msgs=cfg.get('limit_message'),
            max_chars=cfg.get('limit_chars'),
        )
        self._api = OpenAI(
            base_url=f"{cfg['api_host']}/v1",
            api_key=cfg['api_key'],
        )
        self._model: str = cfg['model_name']
        self._temp: float = cfg['temperature']

    def launch(self) -> None:
        self._clear_screen()
        print('Ассистент готов. Модель:', self._model)
        print(
            '\\q — выход | /reset — сброс | '
            '/file_chunk — файл по кускам | @::путь:: — вставить файл'
        )
        print('─' * 40)

        while True:
            try:
                raw = input('\n>>> ').strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not raw:
                continue

            if raw == '\\q':
                print('Выход.')
                break

            if raw == '/reset':
                self._hist.wipe(self._cfg.get('system_prompt'))
                self._clear_screen()
                print('История очищена.')
                continue

            if raw.startswith('/file_chunk'):
                self._do_chunk(raw)
                continue

            cooked = expand_refs(raw)
            self._chat(cooked)

    def _chat(self, text: str) -> None:
        self._hist.push('user', text)
        try:
            stream = self._api.chat.completions.create(
                model=self._model,
                messages=self._hist.clone(),  # type: ignore[arg-type]
                temperature=self._temp,
                stream=True,
            )
            print('', end='', flush=True)
            buf = ''
            try:
                for part in stream:
                    if not hasattr(part, 'choices'):
                        continue
                    chunk: Any = part
                    if chunk.choices and chunk.choices[0].delta.content:
                        tok = chunk.choices[0].delta.content
                        print(tok, end='', flush=True)
                        buf += tok
                print()
            except KeyboardInterrupt:
                print('\n[Прервано]')
            if buf.strip():
                self._hist.push('assistant', buf)
        except Exception:
            print('\n[Ошибка API]')
            self._hist.drop_last()

    def _do_chunk(self, raw: str) -> None:
        args = raw[len('/file_chunk'):].strip()
        mode, val, auto = parse_chunk_cmd(args)

        try:
            path = input('Введите путь до файла: ').strip()
        except (EOFError, KeyboardInterrupt):
            print('\nОтмена.')
            return

        try:
            content = _slurp(path)
        except FileProblem as e:
            print(f'[!] {e}')
            return

        try:
            prompt = input(
                'Принято. Что нужно сделать для каждого фрагмента (User Prompt)?\n> '
            ).strip()
        except (EOFError, KeyboardInterrupt):
            print('\nОтмена.')
            return

        if not prompt:
            print('[!] Нужен промпт.')
            return

        pieces = chunkify(content, mode, val)
        print('Принято. Начинаю обработку:')
        for i, piece in enumerate(pieces, 1):
            if not auto:
                try:
                    input(f'\n[Чанк {i}/{len(pieces)}] <Нажмите Enter для отправки>')
                except (EOFError, KeyboardInterrupt):
                    print('\nПрервано.')
                    return
            else:
                print(f'\n--- Обработка чанка {i}/{len(pieces)} ---')
            self._chat(f'{prompt}\n\n{piece}')
        print('\nОбработка файла завершена.')

    @staticmethod
    def _clear_screen() -> None:
        os.system('cls' if os.name == 'nt' else 'clear')
