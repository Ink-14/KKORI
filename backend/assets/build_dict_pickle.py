"""사전 XML 파일을 pickle로 변환하는 스크립트.

사용법:
    python build_dict_pickle.py <XML_폴더_경로> [-o <출력_pickle_경로>]

예시:
    python build_dict_pickle.py D:/dict_xml
    python build_dict_pickle.py D:/dict_xml -o D:/output/dict.pkl
"""
import argparse
import gzip
import pickle
import re
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).parent))
from bktree import build as build_bktree


def strip_symbols(word: str) -> str:
    """'-', '^' 기호 제거 및 끝부분 숫자 제거한 검색용 단어 반환."""
    word = re.sub(r'[-^]', '', word)
    word = re.sub(r'\d+$', '', word)
    return word


def parse_xml_file(xml_path: Path) -> list[dict]:
    entries = []
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"  [경고] XML 파싱 오류: {xml_path} - {e}", file=sys.stderr)
        return entries

    for item in root.iter('item'):
        word_info = item.find('word_info')
        if word_info is None:
            continue

        word_el = word_info.find('word')
        if word_el is None or not word_el.text:
            continue

        word = word_el.text.strip()
        word_plain = strip_symbols(word)
        if not word_plain:
            continue

        pos_senses = []
        for pos_info in word_info.findall('pos_info'):
            pos_el = pos_info.find('pos')
            pos = pos_el.text.strip() if pos_el is not None and pos_el.text else ''

            senses = []
            for comm_pattern in pos_info.findall('comm_pattern_info'):
                for sense_info in comm_pattern.findall('sense_info'):
                    def_el = sense_info.find('definition')
                    definition = (def_el.text.strip()
                                  if def_el is not None and def_el.text else '')

                    examples = []
                    for ex_info in sense_info.findall('example_info'):
                        ex_el = ex_info.find('example')
                        src_el = ex_info.find('source')
                        ex = (ex_el.text.strip()
                              if ex_el is not None and ex_el.text else '')
                        src = (src_el.text.strip()
                               if src_el is not None and src_el.text else '')
                        if ex:
                            examples.append({'example': ex, 'source': src})

                    if definition:
                        senses.append({'definition': definition, 'examples': examples})

            if pos or senses:
                pos_senses.append({'pos': pos, 'senses': senses})

        entries.append({
            'word': word,
            'word_plain': word_plain,
            'pos_senses': pos_senses,
        })

    return entries


def main():
    parser = argparse.ArgumentParser(
        description='사전 XML 파일들을 하나의 pickle로 변환합니다.'
    )
    parser.add_argument('folder', help='XML 파일이 들어있는 폴더 경로 (하위 폴더 포함)')
    parser.add_argument(
        '-o', '--output',
        default=str(
            Path(__file__).resolve().parent.parent / 'dictionary' / 'dict.pkl'
        ),
        help='출력 pickle 파일 경로 (기본: <프로젝트>/dictionary/dict.pkl)',
    )
    args = parser.parse_args()

    folder = Path(args.folder)
    if not folder.is_dir():
        print(f"오류: 폴더를 찾을 수 없습니다: {folder}", file=sys.stderr)
        sys.exit(1)

    xml_files = sorted(folder.rglob('*.xml'))
    if not xml_files:
        print(f"경고: XML 파일이 없습니다: {folder}", file=sys.stderr)
        sys.exit(1)

    print(f"XML 파일 {len(xml_files)}개 발견, 파싱 시작...")

    all_entries: list[dict] = []
    for i, xml_path in enumerate(xml_files, 1):
        print(f"  [{i:>4}/{len(xml_files)}] {xml_path.name}", end='        \r')
        entries = parse_xml_file(xml_path)
        all_entries.extend(entries)

    print(f"\n총 {len(all_entries):,}개 항목 파싱 완료.")

    print("BK-Tree 구축 중...")
    unique_words = list({e['word_plain'] for e in all_entries})
    bktree = build_bktree(unique_words)
    print(f"BK-Tree 구축 완료 ({len(unique_words):,}개 단어)")

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {"entries": all_entries, "bktree": bktree}
    with gzip.open(output, 'wb', compresslevel=6) as f:
        pickle.dump(payload, f, protocol=pickle.HIGHEST_PROTOCOL)

    size_mb = output.stat().st_size / (1024 * 1024)
    print(f"저장 완료: {output}  ({size_mb:.1f} MB)")


if __name__ == '__main__':
    main()
