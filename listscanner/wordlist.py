from pathlib import Path


def read_wordlist(file_name, extensions):
    words = []
    used = set()

    for line in Path(file_name).read_text(encoding="utf-8").splitlines():
        item = line.strip().lstrip("/")
        if not item or item.startswith("#"):
            continue

        for word in build_words(item, extensions):
            if word not in used:
                used.add(word)
                words.append(word)

    return words


def build_words(item, extensions):
    if "%EXT%" in item:
        return [item.replace("%EXT%", ext) for ext in extensions]

    words = [item]
    name = item.rstrip("/").split("/")[-1]
    is_folder = item.endswith("/")
    has_ext = "." in name
    has_parent_folder = "/" in item.rstrip("/")

    if extensions and not is_folder and not has_ext and not has_parent_folder:
        words.extend(f"{item}.{ext}" for ext in extensions)

    return words
