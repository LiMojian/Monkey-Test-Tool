import tkinter as tk
from tkinter import Scrollbar
import tkinter.messagebox
import subprocess
from third_window import open_third_window
from offline_window import open_offline_window
from tkinter import Toplevel
from tkinter import Tk, PhotoImage

selected_sn = None  # 声明selected_sn为全局变量
listbox = None  # 声明listbox为全局变量
opened_windows = {}  # 定义一个空的字典用于存储打开的窗口


def open_window(selected_sn, window_type):
    global opened_windows  # 声明使用全局变量

    for sn, window in list(opened_windows.items()):
        if window.winfo_exists() and hasattr(window, 'messagebox') and window.messagebox.winfo_exists():
            window.messagebox.destroy()
            opened_windows.pop(sn, None)

    if selected_sn in opened_windows:
        if not opened_windows[selected_sn].winfo_exists():
            opened_windows.pop(selected_sn)
        else:
            opened_windows[selected_sn].focus_force()
            tkinter.messagebox.showinfo("提示", f"已打开 {selected_sn} 的窗口，请勿重复打开")
            return

    if window_type == "online":
        window = open_third_window(selected_sn,opened_windows)
    elif window_type == "offline":
        window = open_offline_window(selected_sn, opened_windows)

    if window:
        opened_windows[selected_sn] = window

def get_connected_devices():
    try:
        devices_output = subprocess.check_output("adb devices", shell=True)
        devices_output = devices_output.decode('utf-8', errors='replace')  # 使用replace处理无法解码的字符
        devices = devices_output.split("\n")[1:-2]  # 剔除输出中的标题和空行
        sn_list = [device.split()[0] for device in devices if device.strip()]  # 提取SN号
        return sn_list
    except UnicodeDecodeError as e:
        tkinter.messagebox.showinfo("UnicodeDecodeError occurred:", e)
        return []

def select_sn():
    global selected_sn
    if not listbox.curselection():
        tkinter.messagebox.showinfo("提示", "请选中SN号后再进行下一步操作")
    else:
        selected_sn = listbox.get(listbox.curselection())
        open_window(selected_sn, "online")

def on_button_click():
    # 清除列表控件信息
    listbox.delete(0, tk.END)
    # 获取连接设备的SN号
    sn_list = get_connected_devices()

    # 将每个SN号添加到Listbox中
    for sn in sn_list:
        listbox.insert(tk.END, sn)

def on_select(event):
    selected_sn.set(listbox.get(listbox.curselection()))

def select_offline_sn():
    global selected_sn
    if not listbox.curselection():
        tkinter.messagebox.showinfo("提示", "请选中SN号后再进行下一步操作")
    else:
        selected_sn = listbox.get(listbox.curselection())
        open_window(selected_sn, "offline")

def open_secondary_window(root):
    # 应用设置图标
    def set_icon():
        icon = PhotoImage(file='monkey.png')
        secondary_window.iconphoto(False, icon)

    global secondary_window, listbox
    secondary_window = tk.Toplevel()
    secondary_window.after(100, set_icon)
    secondary_window.title("King")
    # 设置窗口大小
    secondary_window.geometry("400x300")
    screen_width = secondary_window.winfo_screenwidth()
    screen_height = secondary_window.winfo_screenheight()

    x = (screen_width - 400) // 2
    y = (screen_height - 300) // 2

    # 设置窗口位置
    secondary_window.geometry("+{}+{}".format(x, y))

    # 创建Listbox控件
    listbox = tk.Listbox(secondary_window, selectmode=tk.SINGLE)
    listbox.place(x=10, y=30, width=370, height=100)

    # 创建垂直滚动条
    scrollbar = Scrollbar(secondary_window, orient="vertical")
    scrollbar.place(x=380, y=30, height=100)

    # 将Listbox与滚动条关联
    listbox.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=listbox.yview)

    # 获取连接设备的SN号
    sn_list = get_connected_devices()

    # 将每个SN号添加到Listbox中
    for sn in sn_list:
        listbox.insert(tk.END, sn)

    button = tk.Button(secondary_window, text="在线测试", command=select_sn)
    button.pack(side=tk.TOP, fill=tk.X, padx=80)
    button.place(relx=0.7, rely=0.8, anchor="center")

    button1 = tk.Button(secondary_window, text="离线测试", command=select_offline_sn)
    button1.pack(side=tk.TOP, fill=tk.X, padx=80)
    button1.place(relx=0.3, rely=0.8, anchor="center")

    button = tk.Button(secondary_window, text="刷新已连接设备", command=on_button_click)
    button.place(relx=0.83, rely=0.05, anchor="center")

    label = tk.Label(secondary_window, text="已连接的设备列表：")
    label.place(relx=0.15, rely=0.05, anchor="center")


    def on_secondary_window_close():
        # 关闭已打开的第三窗口和离线窗口
        for window in opened_windows.values():
            if window.winfo_exists():
                window.destroy()

        secondary_window.destroy()  # 销毁窗口2
        root.deiconify()  # 恢复窗口1的显示

    secondary_window.protocol("WM_DELETE_WINDOW", on_secondary_window_close)

    secondary_window.mainloop()

