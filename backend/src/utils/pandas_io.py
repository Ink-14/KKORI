import json

import pandas as pd
from src.models.constants import DEFAULT_EXCEL_COL_NAME

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