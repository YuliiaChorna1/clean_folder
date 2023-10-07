import sys
import re
import shutil
import os
from pathlib import Path


OTHER = "other"
CATEGORIES = {"audio": [".mp3", ".ogg", ".wav", ".amr", ".flac", ".wma"],
              "documents": [".docx", ".txt", ".doc", ".pdf", ".xlsx", ".pptx"],
              "images": [".jpeg", ".png", ".jpg", ".svg"],
              "video": [".avi", ".mp4", ".mov", ".mkv"],
              "archives": [".zip", ".gz", ".tar"],
              OTHER: []
              }
CYRILLIC_SYMBOLS = "абвгдеёжзийклмнопрстуфхцчшщъыьэюяєіїґ"
TRANSLATION = ("a", "b", "v", "g", "d", "e", "e", "j", "z", "i", "j", "k", "l", "m", "n", "o", "p", "r", "s", "t", "u",
               "f", "h", "ts", "ch", "sh", "sch", "", "y", "", "e", "yu", "ya", "je", "i", "ji", "g")
TRANS = {}
EXCLUDED_FOLDERS = set()
STATS = {"Categories": {}, "Known": set(), "Unknown": set()}
REPORT_FILE_NAME = "report.txt"
REPORT_FILE = Path()

def get_categories(file:Path) -> str:
    ext = file.suffix.lower()
    for cat, exts in CATEGORIES.items():
        if ext in exts:
            STATS["Known"].add(ext)
            return cat
    STATS["Unknown"].add(ext)
    return OTHER

def move_file(file:Path, category:str, root_dir:Path, is_normalized:bool=True) -> Path:
    target_dir = root_dir.joinpath(category)
    if not target_dir.exists():
        try:
            target_dir.mkdir()
        except Exception as error:
            print(f"FAILED creating directory '{target_dir}' with error: {error}")
    name = normalize(file.stem) if is_normalized else file.stem
    new_path = target_dir.joinpath(name + file.suffix)
    try:
        file.replace(new_path)
    except Exception as error:
        print(f"FAILED moving file '{file}' with error: {error}")
    return new_path

def sort_folder(path:Path) -> None:
    paths = list(path.glob("**/*"))
    paths.sort(reverse=True)
    for element in paths:
        if is_excluded(element):
            continue
        elif element.is_file():
            category = get_categories(element)
            result_path = None
            if category == "archives":
                result_path = unpack(element, path)
            else:
                result_path = move_file(element, category, path, category!=OTHER)
            STATS["Categories"][category].add(str(result_path))
        elif element.is_dir():
            try:
                element.rmdir()
            except Exception as error:
                print(f"FAILED deleting directory '{element}' with error: {error}")
    
def build_report() -> list:
    report = []
    report.append("Categories")
    for category, paths in STATS["Categories"].items():
        report.append(f"\t{category}")
        report += [f"\t\t{path}" for path in paths]
    report.append("Known")
    report += [f"\t{ext}" for ext in STATS["Known"]]
    report.append("Unknown")
    report += [f"\t{ext}" for ext in STATS["Unknown"]]
    return report

def normalize(file_name:str) -> str:
    translated_name = file_name.translate(TRANS)
    translated_name = re.sub(r"\W", "_", translated_name)
    return translated_name

def unpack(path:Path, target_path: Path) -> Path:
    new_path = path.parent.joinpath(normalize(path.stem) + path.suffix)
    path.rename(new_path)
    result_path = target_path.joinpath("archives", new_path.stem)
    try:
        shutil.unpack_archive(new_path, result_path)
    except Exception as error:
        print(f"FAILED unpacking archive '{new_path}' with error: {error}")
    try:
        new_path.unlink()
    except Exception as error:
        print(f"FAILED deleting archive '{new_path}' with error: {error}")
    return result_path

def initialize(path:Path) -> None:
    global EXCLUDED_FOLDERS, REPORT_FILE, TRANS
    TRANS = {key:value for c, l in zip(CYRILLIC_SYMBOLS, TRANSLATION) for key,value in ((ord(c), l), (ord(c.title()), l.title()))}
    # for c, l in zip(CYRILLIC_SYMBOLS, TRANSLATION):
    #     TRANS[ord(c)] = l
    #     TRANS[ord(c.title())] = l.title()
    EXCLUDED_FOLDERS = {path.joinpath(key) for key in CATEGORIES.keys()}
    STATS["Categories"] = {category:set() for category in CATEGORIES.keys()}
    REPORT_FILE = path.joinpath(REPORT_FILE_NAME)
    
def is_excluded(path:Path) -> bool:
    for el in EXCLUDED_FOLDERS:
        if path.is_relative_to(el) or path == el:
            return True
    if path == REPORT_FILE:
        return True
    return False

def save_report(report) -> None:
    try:
        with open(REPORT_FILE, "w") as fh:
            fh.write("\n".join(report))
    except Exception as error:
        print(f"FAILED saving report in file with error: {error}")
        print(report)

def main():
    try:
        path = Path(sys.argv[1])
        # path = Path(r"C:\Test_HW")
    except IndexError:
        return "No path to folder"

    if not path.exists():
        return "Folder doesn't exist"
    
    initialize(path)
    sort_folder(path)
    save_report(build_report())
    
    return "Sorted successfully"


if __name__ == "__main__":
    print(main())