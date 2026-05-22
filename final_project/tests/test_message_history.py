from app.message_history import History


def test_empty() -> None:
    h = History()
    assert h.clone() == []


def test_with_system() -> None:
    h = History(system='Ты бот')
    assert len(h.clone()) == 1
    assert h.clone()[0]['role'] == 'system'


def test_push_and_clone() -> None:
    h = History()
    h.push('user', 'Привет')
    h.push('assistant', 'Здравствуй')
    msgs = h.clone()
    assert len(msgs) == 2
    assert msgs[0]['content'] == 'Привет'
    assert msgs[1]['content'] == 'Здравствуй'


def test_drop_last() -> None:
    h = History()
    h.push('user', 'A')
    h.drop_last()
    assert h.clone() == []


def test_wipe() -> None:
    h = History(system='sys')
    h.push('user', 'Q')
    h.wipe(system='new_sys')
    msgs = h.clone()
    assert len(msgs) == 1
    assert msgs[0]['content'] == 'new_sys'


def test_max_messages() -> None:
    h = History(max_msgs=2)
    h.push('user', 'A')
    h.push('assistant', 'B')
    h.push('user', 'C')
    msgs = h.clone()
    assert len(msgs) == 2
    assert msgs[0]['content'] == 'B'
    assert msgs[1]['content'] == 'C'


def test_max_messages_preserves_system() -> None:
    h = History(system='sys', max_msgs=1)
    h.push('user', 'Q')
    h.push('assistant', 'A')
    msgs = h.clone()
    assert len(msgs) == 2
    assert msgs[0]['role'] == 'system'


def test_max_chars_single() -> None:
    h = History(max_chars=5)
    h.push('user', 'ABCDEFGH')
    msg = h.clone()[0]
    assert len(msg['content']) == 5
    assert msg['content'] == 'DEFGH'


def test_max_chars_multi() -> None:
    h = History(max_chars=8)
    h.push('user', 'Hello')
    h.push('assistant', 'World!')
    msgs = h.clone()
    assert len(msgs) == 1
    assert msgs[0]['content'] == 'World!'