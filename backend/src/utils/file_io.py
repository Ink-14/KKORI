import warnings
from pathlib import Path
import csv

from src.models.interface import Tag
from src.models.constants import DEFAULT_TERMBASE_COL_NAME

warnings.filterwarnings('ignore', message='Data Validation extension is not supported')

def make_dictionary_list(dictionary_file_name: Path) -> list[tuple[str, Tag, int]]:
	result = []
	with open(dictionary_file_name, encoding='utf-8', newline='') as f:
		reader = csv.DictReader(f)

		for _, row in enumerate(reader, start=2):
			word = row.get("word", "")
			category = row.get("category", "")
			score = row.get("score", "") or "0"

			if not word:
				raise ValueError(f"word column has empty values!\n{row}")
			if not category:
				raise ValueError(f"category column has empty values!\n{row}")

			result.append((word, Tag[category], int(score)))
	return result

def make_pre_analyzed_dict_list(dictionary_file_name: Path) -> list[tuple[str, list[tuple[str, Tag]], float]]:
	result = []
	with open(dictionary_file_name, encoding='utf-8', newline='') as f:
		reader = csv.reader(f)
		next(reader, None)
		
		for row in reader:
			if not row or not row[0]:
				continue

			word = row[0]
			score = float(row[1]) if row[1] else 0.0

			rest = row[2:]
			
			if len(rest) % 2 != 0:
				raise ValueError(f"Form and Tag mismatched: {row}")
			
			result.append((word, [(rest[i], Tag[rest[i+1]].value) for i in range(0, len(rest), 2)], score))
	return result

def make_termbase_list(termbase_file_name: Path, col_names: list[str] = None) -> list[str]:
	if col_names is None:
		col_names = [DEFAULT_TERMBASE_COL_NAME]

	result = []

	with open(termbase_file_name, encoding='utf-8', newline='') as f:
		reader = csv.DictReader(f)
		for row in reader:
			value = row.get(DEFAULT_TERMBASE_COL_NAME, "")
			result.append(value if value is not None else "")
	return result

def make_word_and_score_list(word_file_name: Path, skip_empty_rows: bool = True) -> list[tuple[str, float]]:
	result = []
	with open(word_file_name, encoding='utf-8', newline='') as f:
		reader = csv.DictReader(f)
		for _, row in enumerate(reader, start=2):
			word = row.get("word", "")
			score = row.get("score", "0")
			if not score:
				score = 0
			
			if skip_empty_rows:
				if not word:
					continue

			result.append((word, float(score)))
	return result

def get_all_file_paths(folder_name: str, extension: str = None) -> list[Path]:
	if extension is None:
		target_path = Path(folder_name).rglob("*")
	else:
		target_path = Path(folder_name).rglob(f"*.{extension}")

	return [i.absolute() for i in target_path if i.is_file() and not i.name.startswith("~$")]

def read_txt_lines(file_path: str, drop_empty: bool = False) -> list[str]:
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()

    if drop_empty:
        lines = [l for l in lines if l.strip()]

    return lines