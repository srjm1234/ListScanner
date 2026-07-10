import configparser


DEFAULT_SETTINGS = {
    "wordlist": "dictionary/wordlist.txt",
    "extensions": "php,html,bak,zip",
    "threads": 10,
    "timeout": 5,
    "output": "report.html",
}


def load_settings(config_file="config.ini"):
    config = configparser.ConfigParser()
    config.read(config_file, encoding="utf-8")

    section = config["scanner"] if "scanner" in config else {}

    return {
        "wordlist": section.get("wordlist", DEFAULT_SETTINGS["wordlist"]),
        "extensions": section.get("extensions", DEFAULT_SETTINGS["extensions"]),
        "threads": _to_int(section.get("threads"), DEFAULT_SETTINGS["threads"]),
        "timeout": _to_float(section.get("timeout"), DEFAULT_SETTINGS["timeout"]),
        "output": section.get("output", DEFAULT_SETTINGS["output"]),
    }


def _to_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_float(value, default):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
