from ctypes import windll, wintypes
import ctypes
import json
import os


def get_documents_folder():
    CSIDL_PERSONAL = 5
    SHGFP_TYPE_CURRENT = 0
    buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
    windll.shell32.SHGetFolderPathW(None, CSIDL_PERSONAL, None, SHGFP_TYPE_CURRENT, buf)
    return buf.value

DOCUMENTS_FOLDER = os.path.join(get_documents_folder(), "NoMoreBorder")
SETTINGS_FILE_PATH = os.path.join(DOCUMENTS_FOLDER, "settings.json")

def load_settings():
    if not os.path.exists(DOCUMENTS_FOLDER):
        os.makedirs(DOCUMENTS_FOLDER)

    try:
        with open(SETTINGS_FILE_PATH, "r") as f:
            settings = json.load(f)
            if isinstance(settings["apps"], list):
                settings["apps"] = {app: {
                    "monitor": "Display 1 (Primary)",
                    "resolution": "Use Display Resolution",
                    "x_offset": "0",
                    "y_offset": "0",
                    "width": "1920",
                    "height": "1080"
                } for app in settings["apps"]}
                save_settings(settings)
            if "start_with_windows" not in settings:
                settings["start_with_windows"] = False
            return settings
    except:
        return {"theme": "System", "apps": {}, "start_with_windows": False}


def save_settings(settings):
    try:
        with open(SETTINGS_FILE_PATH, "w") as f:
            json.dump(settings, f, indent=4)
    except:
        pass