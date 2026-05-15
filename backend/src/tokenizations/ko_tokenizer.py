from contextlib import contextmanager
from pathlib import Path

from kiwipiepy import Kiwi

from src.utils.file_io import get_all_file_paths, make_dictionary_list, make_termbase_list, make_pre_analyzed_dict_list
from src.models.interface import Tag

class KoTokenizer(Kiwi):
    _instance = None
    DEFAULT_DICTIONARY_PATH = Path(__file__).parent
    DEFAULT_TERMBASE_PATH = Path(__file__).parent.parent.parent / "termbase"

    DEFAULT_KO_DICT_FILE_NAME = "ko_dictionary"
    DEFAULT_PRE_ANALYZED_DICT_FILE_NAME = "ko_preanalyzed"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not getattr(self, '_initialized', False):
            super().__init__(model_type='cong-global')
            
            self._debug = False
            self._make_dictionary()
            self._add_termbase()
            self._initialized = True

    def _make_dictionary(self):
        dictionary_files = get_all_file_paths(self.DEFAULT_DICTIONARY_PATH, "csv")
        for file in dictionary_files:
            if file.stem == self.DEFAULT_KO_DICT_FILE_NAME:
                for words in make_dictionary_list(file):
                    word, tag, score = words
                    self.add_user_word(word=word, tag=tag, score=score)
            elif file.stem == self.DEFAULT_PRE_ANALYZED_DICT_FILE_NAME:
                for words in make_pre_analyzed_dict_list(file):
                    word, form_tags, score = words
                    self.add_pre_analyzed_word(word, form_tags, score)

    def _add_termbase(self):
        termbase_files = get_all_file_paths(self.DEFAULT_TERMBASE_PATH, "csv")
        for file in termbase_files:
            for word in make_termbase_list(file):
                self.add_user_word(word, Tag.일반명사)        

    def tokenize(self, *args, **kwargs):
        return super().tokenize(*args, **kwargs)

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, value: bool):
        print(f"[KoTokenizer] Debug mode switched to {value}")
        self._debug = value

    @classmethod
    def reset(cls):
        """싱글톤 인스턴스를 초기화하고 새로 생성하는 함수."""
        cls._instance = None
        return cls()

    @contextmanager
    def debug_mode(self):
        """
        디버깅 모드 실행. with문과 함께 사용할 것.

        사용 예시

        with KoTokenizer().debug_mode():
             check_spelling(...)
        """
        original_status = self.debug
        self.debug = True
        try:
            yield
        finally:
            self.debug = original_status