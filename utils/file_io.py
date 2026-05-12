import warnings
from pathlib import Path
import json

import pandas as pd
import csv

from korean_spell_checker.models.interface import Tag
from korean_spell_checker.models.constants import DEFAULT_EXCEL_COL_NAME, DEFAULT_TERMBASE_COL_NAME

warnings.filterwarnings('ignore', message='Data Validation extension is not supported')

def make_dictionary_list(dictionary_file_name: Path) -> list[tuple[str, Tag, int]]:
	df = pd.read_csv(dictionary_file_name, dtype=str)
	if df["word"].isna().any() or (df["word"] == "").any():
		raise ValueError("word column has empty values")
	if df["category"].isna().any() or (df["category"] == "").any():
		raise ValueError("category column has empty values")
	df["score"] = df["score"].fillna("0").replace("", "0")

	return [(row.word, Tag[row.category], int(row.score)) for row in df.itertuples(index=False)] # type: ignore

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
	df = pd.read_csv(termbase_file_name, usecols=col_names, dtype=str)
	return [i for i in df[DEFAULT_TERMBASE_COL_NAME]]

def get_all_file_paths(folder_name: str, extension: str = None) -> list[Path]:
	if extension is None:
		target_path = Path(folder_name).rglob("*")
	else:
		target_path = Path(folder_name).rglob(f"*.{extension}")
	return [i.absolute() for i in target_path if i.is_file() and not i.name.startswith("~$")]

def read_excel_file(file_path: str, col_names: list[str] = None, drop_na: bool = False) -> pd.DataFrame:
	if col_names is None:
		col_names = [DEFAULT_EXCEL_COL_NAME]
	df = pd.read_excel(file_path, usecols=col_names, dtype=str)
	if drop_na:
		df = df.dropna()
	return df

def read_txt_file(file_path: str, drop_na: bool = False) -> pd.DataFrame:
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()
    df = pd.DataFrame(lines, columns=['text'])
    if drop_na:
        df = df.dropna()
    return df

def read_json_file(file_path: str, drop_na: bool = False) -> pd.DataFrame:
    with open(file_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    data = raw_data.values()
    df = pd.DataFrame(data, columns=['text'])
    if drop_na:
        df = df.dropna()
    return df