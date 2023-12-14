import sys
import re
import shutil
import concurrent.futures
from pathlib import Path
from threading import RLock


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
STATS = {"Categories": {}, "Known": set(), "Unknown": set()}
excluded_folders = set()
report_file_name = "report.txt"
report_file = Path()
folders_to_delete = set()
root_path = Path()
lock = RLock()

def get_categories(file:Path) -> str:

    ext = file.suffix.lower()

    for cat, exts in CATEGORIES.items():
        if ext in exts:
            STATS["Known"].add(ext)
            return cat
        
    STATS["Unknown"].add(ext)
    return OTHER


def move_file(file:Path, category:str, is_normalized:bool=True) -> Path:

    target_dir = root_path.joinpath(category)

    with lock:
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


def process_element(element: Path) -> None:

    if is_excluded(element):
        return

    elif element.is_file():
        category = get_categories(element)
        result_path = None
        if category == "archives":
            result_path = unpack(element)
        else:
            result_path = move_file(element, category, category!=OTHER)
        
        STATS["Categories"][category].add(str(result_path))

    elif element.is_dir():

        folders_to_delete.add(element)
        
        
def delete_empty_folders():
    
    folders_list = list(folders_to_delete)
    folders_list.sort(reverse=True)

    for folder in folders_list:
        try:
            folder.rmdir()
        except Exception as error:
            print(f"FAILED deleting directory '{folder}' with error: {error}")


def sort_folder() -> None:

    paths = list(root_path.glob("**/*"))
    paths.sort(reverse=True)

    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        
        executor.map(process_element, paths)
    
    delete_empty_folders()


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


def unpack(path:Path) -> Path:

    new_path = path.parent.joinpath(normalize(path.stem) + path.suffix)
    path.rename(new_path)
    result_path = root_path.joinpath("archives", new_path.stem)

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

    global excluded_folders, report_file, TRANS, root_path
    TRANS = {key:value for c, l in zip(CYRILLIC_SYMBOLS, TRANSLATION) for key,value in ((ord(c), l), (ord(c.title()), l.title()))}
    # for c, l in zip(CYRILLIC_SYMBOLS, TRANSLATION):
    #     TRANS[ord(c)] = l
    #     TRANS[ord(c.title())] = l.title()
    excluded_folders = {path.joinpath(key) for key in CATEGORIES.keys()}
    STATS["Categories"] = {category:set() for category in CATEGORIES.keys()}
    report_file = path.joinpath(report_file_name)
    root_path = path


def is_excluded(path:Path) -> bool:

    for el in excluded_folders:
        if path.is_relative_to(el) or path == el:
            return True
        
    if path == report_file:
        return True
    
    return False


def save_report(report) -> None:

    try:
        with open(report_file, "w") as fh:
            fh.write("\n".join(report))
    except Exception as error:
        print(f"FAILED saving report in file with error: {error}")
        print(report)


def main() -> str:

    try:
        path = Path(sys.argv[1])
        # path = Path(r"C:\Test_HW")
    except IndexError:
        return "No path to folder"

    if not path.exists():
        return "Folder doesn't exist"
    
    initialize(path)
    sort_folder()
    save_report(build_report())
    
    return "Sorted successfully"


if __name__ == "__main__":
    
    print(main())
