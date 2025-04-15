import customtkinter as ctk
import ctypes, sys
import time
import win32gui
import win32con
import json, os
import threading
import winreg as reg
from PIL import Image, ImageDraw
from pystray import Icon, MenuItem, Menu
from threading import Thread
from screeninfo import get_monitors
from ctypes import wintypes, windll
from settings import Settings
import settings_utils
import ui_helper


user32 = ctypes.windll.user32
screen_width, screen_height = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
Geometry = "400x380+" + str(int(screen_width/2) - 200) + '+' + str(int(screen_height/2) - 200)
selected_app = "0"
windowList, saveList, monitors = [], {}, {}
exact_match, selected_monitor, tray_icon = False, None, None
my_settings = Settings()

# Get monitor info from screeninfo
for index, m in enumerate(get_monitors()):
    name = f"Display {str(index + 1)}"
    if(m.is_primary):
        name += " (Primary)"
        selected_monitor = name
    monitors[name] = m

def enum_window_proc(hwnd, resultList):
    if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
        resultList.append((hwnd, win32gui.GetWindowText(hwnd)))

def update_window_list():
    global windowList, saveList, selected_app, selected_monitor

    while True:
        temp = []
        win32gui.EnumWindows(enum_window_proc, temp)

        temp_titles = [title for hwnd, title in temp]
        for save_item in saveList:
            for temp_title in temp_titles:
                if temp_title.startswith(save_item):
                    # Use saved settings if they exist
                    make_borderless(save_item, write_needed=False)

        if windowList != temp:
            try:
                panel.after(20, refresh_window_list)
            except:
                exit()

        windowList = temp
        time.sleep(2)

def refresh_window_list():
    global window_list_dropdown, windowList
    windowList_strings = [title for hwnd, title in windowList]
    window_list_dropdown.configure(values=windowList_strings)

def exact_match_event():
    global exact_match_check, exact_match
    exact_match = exact_match_check.get() == 1

def change_start_with_windows_event():
    global check_box
    settings = settings.load_settings()
    start_with_windows = check_box.get() == 1
    settings["start_with_windows"] = start_with_windows
    set_startup(start_with_windows)
    settings.save_settings(settings)

def update_element(elem_name, elem_ref):
    settings = settings.load_settings()
    settings[elem_name] = elem_ref
    settings.save_settings(settings)

def change_appearance_mode_event(new_appearance_mode: str):
    ctk.set_appearance_mode(new_appearance_mode)
    update_element("theme", new_appearance_mode)


def combo_answer(choice):
    global selected_app
    selected_app = choice

    if choice in saveList:
        custom_x_offset.set(saveList[choice]["x_offset"])
        custom_y_offset.set(saveList[choice]["y_offset"])
        custom_width.set(saveList[choice]["width"])
        custom_height.set(saveList[choice]["height"])
        exact_match = saveList[choice]["exact_match"]
        if exact_match_check.get() != (1 if exact_match else 0):
           exact_match_check.toggle()
    else:
        custom_x_offset.set("0")
        custom_y_offset.set("0")
        custom_width.set(str(monitors[selected_monitor].width))
        custom_height.set(str(monitors[selected_monitor].height))

def combo_answer_display(choice):
    global selected_monitor
    selected_monitor = choice
    label.configure(text="Display Resolution is " + str(monitors[choice].width) + 'x' + str(monitors[choice].height))

    if selected_app not in saveList:
        custom_width.set(str(monitors[selected_monitor].width))
        custom_height.set(str(monitors[selected_monitor].height))

def get_window(app_name, exact_match):
    global windowList
    hwnd = None
    for win_hwnd, win_title in windowList:
        if (win_title == app_name if exact_match else win_title.startswith(app_name)):
            hwnd = win_hwnd
            break

    return hwnd

def make_borderless(app_name=None, write_needed=True):
    global selected_app, windowList, saveList, custom_x_offset, custom_y_offset, custom_width, custom_height, selected_monitor, exact_match

    app_name = app_name or selected_app
    exact = exact_match if write_needed else saveList[app_name].get("exact_match")
    exact = False if exact is None else exact
    hwnd = get_window(app_name, exact)
    if hwnd is None:
        return

    try:
        if write_needed:
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            pre_win_height = bottom - top
            pre_win_width = right - left

        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE) & ~(win32con.WS_CAPTION) & ~(win32con.WS_THICKFRAME)
        win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)

        if write_needed:
            target_resolution = (int(custom_width.get()), int(custom_height.get()))
            location_x = monitors[selected_monitor].x + int(custom_x_offset.get())
            location_y = monitors[selected_monitor].y + int(custom_y_offset.get())
        else:
            target_resolution = (int(saveList[app_name]["width"]), int(saveList[app_name]["height"]))
            location_x = monitors[saveList[app_name]["monitor"]].x + int(saveList[app_name]["x_offset"])
            location_y = monitors[saveList[app_name]["monitor"]].y + int(saveList[app_name]["y_offset"])

        win32gui.MoveWindow(hwnd, location_x, location_y, target_resolution[0], target_resolution[1], True)
        win32gui.SetWindowPos(hwnd, None, location_x, location_y, target_resolution[0], target_resolution[1], win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED)

        if write_needed:
            saveList[app_name] = {}
            saveList[app_name]["monitor"] = selected_monitor
            saveList[app_name]["x_offset"] = custom_x_offset.get()
            saveList[app_name]["y_offset"] = custom_y_offset.get()
            saveList[app_name]["width"] = custom_width.get()
            saveList[app_name]["height"] = custom_height.get()
            saveList[app_name]["pre_win_height"] = pre_win_height
            saveList[app_name]["pre_win_width"] = pre_win_width
            saveList[app_name]["exact_match"] = exact_match
            update_element("apps", saveList)

    except win32gui.error as e:
        if e.winerror == 1400:
            print(e)
            pass

def restore_window():
    global selected_app, windowList, saveList, exact_match

    app_name = selected_app

    if app_name != "0":
        pre_win_height = saveList[app_name]["pre_win_height"]
        pre_win_width = saveList[app_name]["pre_win_width"]

        hwnd = get_window(app_name, saveList[app_name].get("exact_match") or exact_match)
        if hwnd is None:
            return

        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE) | win32con.WS_CAPTION | win32con.WS_SYSMENU | win32con.WS_MINIMIZEBOX | win32con.WS_MAXIMIZEBOX | win32con.WS_THICKFRAME
        win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)

        win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, 350, 200, pre_win_width, pre_win_height, win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED)

        if app_name in saveList:
            saveList.pop(app_name)
            update_element("apps", saveList)

def on_quit(icon, item):
    icon.stop()
    panel.after(0, panel.quit)

def on_show(icon, item):
    global tray_icon
    icon.stop()

    panel.geometry(Geometry)

    def do1():
        panel.attributes("-alpha", 0)
    panel.after(10, do1())

    panel.deiconify()
    panel.update_idletasks()
    panel.update()

    def do2():
        panel.attributes("-alpha", 1)
    panel.after(1000, do2())

    tray_icon = None

def create_custom_icon():
    image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    draw.rectangle([0, 0, 64, 64], fill=(0, 156, 255, 255))
    draw.rectangle([16, 16, 64, 48], fill=(0, 0, 0, 0))
    draw.rectangle([48, 16, 64, 48], fill=(0, 98, 177, 255))
    return image

def minimize_to_tray(event=None):
    global tray_icon
    panel.withdraw()
    if tray_icon is None:
        menu = Menu(
            MenuItem('Show', on_show),
            MenuItem('Quit', on_quit)
        )
        tray_icon = Icon("NoMoreBorder", create_custom_icon(), "NoMoreBorder", menu)
        threading.Thread(target=tray_icon.run, daemon=True).start()

def set_startup(startup):
    s_name = "NoMoreBorder"
    address = sys.executable
    key = r"Software\Microsoft\Windows\CurrentVersion\Run"

    open_key = reg.OpenKey(reg.HKEY_CURRENT_USER, key, 0, reg.KEY_ALL_ACCESS)

    if startup:
        reg.SetValueEx(open_key, s_name, 0, reg.REG_SZ, address)
    else:
        try:
            reg.DeleteValue(open_key, s_name)
        except FileNotFoundError:
            pass
    reg.CloseKey(open_key)

current_settings = settings_utils.load_settings()
saveList = current_settings["apps"]
ctk.set_appearance_mode(current_settings["theme"])
ctk.set_default_color_theme("blue")  # Themes: "blue" / "green" / "dark-blue"

panel = ctk.CTk()
panel.geometry(Geometry)
panel.resizable(False, False)
panel.grid_columnconfigure(0, weight=1)
panel.title('NoMoreBorder')

if current_settings["start_with_windows"] == True:
    minimize_to_tray()

label = ctk.CTkLabel(panel, text="Display Resolution is " + str(monitors[selected_monitor].width) + 'x' + str(monitors[selected_monitor].height), font=("Helvetica", 20))
label.grid(row=0, column=0, pady=(20, 10), columnspan=2)

window_panel = ctk.CTkFrame(panel, fg_color="transparent")
window_panel.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
window_panel.grid_columnconfigure(0, weight=1)

window_list_dropdown = ctk.CTkComboBox(window_panel, values=["Select Application"], command=combo_answer)
window_list_dropdown.grid(row=0, column=0, padx=(0, 10), sticky="ew")

exact_match_check = ctk.CTkCheckBox(window_panel, text='Exact Match', command=exact_match_event)
exact_match_check.grid(row=0, column=1, sticky="e")

monitor_dropdown = ctk.CTkComboBox(panel, values=list(monitors.keys()), width=400, command=combo_answer_display)
monitor_dropdown.set(selected_monitor)
monitor_dropdown.grid(row=2, column=0, columnspan=2, padx=20, pady=(0, 10))

from tkinter import StringVar

custom_x_offset = StringVar(value="0")
custom_y_offset = StringVar(value="0")
custom_width = StringVar(value=str(monitors[selected_monitor].width))
custom_height = StringVar(value=str(monitors[selected_monitor].height))

custom_res_frame = ctk.CTkFrame(panel, fg_color="transparent")
custom_res_frame.grid(pady=5)

ui_helper.add_entry_with_label(custom_res_frame, "X Offset:", custom_x_offset, 0,0)
ui_helper.add_entry_with_label(custom_res_frame, "Width:", custom_y_offset, row=0,col=2)
ui_helper.add_entry_with_label(custom_res_frame, "Width:", custom_width, row=1,col=0)
ui_helper.add_entry_with_label(custom_res_frame, "Height:", custom_height, row=1,col=2)

buttons_frame = ctk.CTkFrame(panel, fg_color="transparent")
buttons_frame.grid(pady=5)

submit_button = ctk.CTkButton(buttons_frame, text="Make it Borderless", command=make_borderless, height=35)
submit_button.grid(row=0, column=0, padx=5)

undo_button = ctk.CTkButton(buttons_frame, text="Undo Lmao!", command=restore_window, height=35)
undo_button.grid(row=0, column=1, padx=5)

check_box = ctk.CTkCheckBox(panel, text='Start with Windows', command=change_start_with_windows_event)
check_box.grid(padx=5, pady=(15, 0))
check_box.select() if current_settings["start_with_windows"] else check_box.deselect()

buttons_frame2 = ctk.CTkFrame(panel, fg_color="transparent")
buttons_frame2.grid()

toggle_mode = ctk.CTkLabel(buttons_frame2, text="Appearance Mode:", anchor="w")
toggle_mode.grid(row=1, column=0, padx=5, pady=5)

toggle_mode_options = ctk.CTkOptionMenu(buttons_frame2, values=my_settings.available_themes, command=change_appearance_mode_event, width=100, height=22)
toggle_mode_options.grid(row=1, column=1, padx=10, pady=5)
toggle_mode_options.set(current_settings["theme"])

Thread(target=update_window_list).start()

print(my_settings.start_with_system)

panel.bind('<Unmap>', minimize_to_tray)
panel.mainloop()

if tray_icon is not None:
    tray_icon.stop()
