import asyncio
from copy import deepcopy

import pytest

from src import api
from src.engines.raw_searcher import RawStringSearcher
from src.models.interface import SpellErrorType


def make_searcher(words):
    searcher = RawStringSearcher()
    searcher.add_word_from_list([
        ([(tuple(words), "test")], SpellErrorType.SPELLING_RAW, "test")
    ])
    return searcher


@pytest.mark.parametrize("batch", [False, True])
def test_replace_and_clear_whitelist_after_search(batch):
    searcher = make_searcher(["alpha", "beta"])

    def errors(text):
        return searcher.search_batch([text])[0] if batch else searcher.search(text)

    searcher.set_whitelist_words(["alpha"])
    assert errors("alpha") == []
    assert errors("beta")
    searcher.set_whitelist_words(["beta"])
    assert errors("alpha")
    assert errors("beta") == []
    searcher.set_whitelist_words([])
    assert errors("beta")


class FakeTokenizer:
    @classmethod
    def reset(cls):
        return cls()

    def tokenize(self, text):
        return []

    def add_user_word(self, *args):
        pass


@pytest.fixture
def dictionary_api(monkeypatch):
    monkeypatch.setattr(api, "KoTokenizer", FakeTokenizer)
    monkeypatch.setattr(api, "_tokenizer", None)
    monkeypatch.setattr(api, "_tokenizer_lock", asyncio.Lock())
    data = {}

    def save_data(updated):
        data.clear()
        data.update(deepcopy(updated))

    monkeypatch.setattr(api, "_load_user_data", lambda: deepcopy(data))
    monkeypatch.setattr(api, "_save_user_data", save_data)
    monkeypatch.setattr(api, "RAW_WHITELISTS", ["default"])
    searcher = make_searcher(["default", "globalword", "alpha", "beta"])
    monkeypatch.setattr(api, "_raw_searcher", searcher)
    return searcher


def test_project_switch_delete_and_word_removal(dictionary_api):
    searcher = dictionary_api
    api._save_user_data({
        "global": [{"word": "globalword", "tag": "고유명사"}],
        "projects": {
            "A": [{"word": "alpha", "tag": "고유명사"}],
            "B": [{"word": "beta", "tag": "고유명사"}],
        },
        "active_project": None,
    })

    async def scenario():
        await api.activate_project(api.ActivateProjectRequest(project="A"))
        assert searcher.search("alpha") == []
        assert searcher.search("beta")
        await api.activate_project(api.ActivateProjectRequest(project="B"))
        assert searcher.search("alpha")
        assert searcher.search("beta") == []
        assert searcher.search("globalword") == []
        await api.delete_project("B")
        assert searcher.search("beta")
        await api.add_words(api.AddWordsRequest(words=[], scope="global"))
        assert searcher.search("globalword")
        assert searcher.search("default") == []

    asyncio.run(scenario())


def test_startup_loads_default_and_user_whitelist(dictionary_api, monkeypatch):
    monkeypatch.setattr(api, "RAW_STRING_RULES", [
        ([(('default', 'alpha', 'a'), 'test')], SpellErrorType.SPELLING_RAW, 'test')
    ])
    monkeypatch.setattr(api, "SPELL_CHECK_RULES", [])
    monkeypatch.setattr(api, "_spell_checker", None)
    api._save_user_data({
        "global": [{"word": "alpha", "tag": "고유명사"}],
        "projects": {},
        "active_project": None,
    })

    async def scenario():
        async with api.lifespan(None):
            assert api._raw_searcher.search("default") == []
            assert api._raw_searcher.search("alpha") == []
            assert api._raw_searcher.search("a")

    asyncio.run(scenario())
