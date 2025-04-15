class Settings():
    theme = "System"
    available_themes = ["System", "Dark", "Light"]
    start_with_system = False
    apps = list()

class App():
    name = ""
    monitor = ""
    x_offset = 0
    y_offset = 0
    width = 0
    height = 0
    pre_win_height = 0
    pre_win_width = 0
    exact_match = False

    def __init__(self):
        pass
