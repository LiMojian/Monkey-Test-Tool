import tkinter as tk
from tkinter import Scrollbar
import tkinter.messagebox
import subprocess
from tkinter import ttk
import datetime
import os
import signal
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import json
import os
from tkinter import Tk, PhotoImage


def open_offline_window(selected_sn,opened_windows):
    if selected_sn in opened_windows:
        if not opened_windows[selected_sn].winfo_exists():  # 检查窗口是否存在
            opened_windows.pop(selected_sn)  # 如果窗口不存在，则从字典中移除
        else:
            tkinter.messagebox.showinfo("提示", f"已打开 {selected_sn} 的窗口，请勿重复打开")
            return None

    # 应用设置图标
    def set_icon():
        icon = PhotoImage(file='monkey.png')
        offline_window.iconphoto(False, icon)

    offline_window = tk.Toplevel()
    offline_window.after(100, set_icon)
    offline_window.title("{}-离线测试".format(selected_sn))
    # 设置窗口大小
    offline_window.geometry("800x600")

    # 获取屏幕宽度和高度
    screen_width = offline_window.winfo_screenwidth()
    screen_height = offline_window.winfo_screenheight()

    # 计算窗口位置
    x = (screen_width - 800) // 2
    y = (screen_height - 600) // 2

    # 设置窗口位置
    offline_window.geometry("+{}+{}".format(x, y))

    # 创建Listbox表格
    listbox1 = tk.Listbox(offline_window, selectmode=tk.MULTIPLE)
    listbox1.place(x=10, y=30, width=370, height=320)

    # 创建垂直滚动条
    scrollbar = Scrollbar(offline_window, orient="vertical")
    scrollbar.place(x=380, y=30, height=320)

    listbox1.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=listbox1.yview)

    package_names = []
    adb_command = "adb -s {} shell pm list packages".format(selected_sn)
    result = subprocess.Popen(adb_command, shell=True, stdout=subprocess.PIPE).stdout.read().decode('utf-8')
    for line in result.splitlines():
        package_names.append(line.split(":")[-1])

    # 对包名列表进行排序
    package_names.sort()

    # 在Listbox中添加多选框和包名
    for package in package_names:
        listbox1.insert(tk.END, f"{package}")

    selected_indices = []  # 用于记录选中的包名索引
    last_selected_indices = []  # 用于记录上一次选中的包名索引
    mouse_pressed_on_search_entry = False  # 标记鼠标是否在搜索框上按下

    def search_packages():
        search_text = search_var.get()
        listbox1.delete(0, tk.END)
        for i, package in enumerate(package_names):
            if search_text.lower() in package.lower():
                listbox1.insert(tk.END, f"{package}")
                if i in last_selected_indices:  # 如果索引在上一次选中的索引列表中
                    listbox1.select_set(tk.END)  # 选中该包名

    def on_select(event):
        selected_items = listbox1.curselection()
        for item in selected_items:
            if item not in selected_indices:
                selected_indices.append(item)

    def run_command(command):
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)
        output, _ = process.communicate()
        return output.decode('utf-8')

    def run_logcat():
        logcat_time = search_logcat_time.get()
        text.insert(tk.END, "{}:开始抓取logcat日志\n".format(datetime.datetime.now()))
        logcat_command = "nohup sh -c 'logcat >monkey/logcat.txt & sleep {} &&kill -SIGINT $!'&".format(logcat_time)
        adb_command_logcat = 'adb -s {} shell "cd sdcard; {}"'.format(selected_sn, logcat_command)
        run_command(adb_command_logcat)

    def check_monkey():
        output = subprocess.run("adb -s {} shell ls /sdcard/monkey".format(selected_sn), shell=True,
                                capture_output=True,
                                text=True)
        if output.returncode == 0:
            subprocess.run("adb -s {} shell rm /sdcard/monkey".format(selected_sn), shell=True)
            subprocess.run("adb -s {} shell mkdir sdcard/monkey".format(selected_sn), shell=True)
            text.insert(tk.END, "{}:已创建monkey文件夹\n".format(datetime.datetime.now()))
        else:
            subprocess.run("adb -s {} shell mkdir sdcard/monkey".format(selected_sn), shell=True)
            text.insert(tk.END, "{}:已创建monkey文件夹\n".format(datetime.datetime.now()))

    def check_monkey_log():
        output = subprocess.run("adb -s {} shell ls /sdcard/monkey/monkey_log.txt".format(selected_sn), shell=True,
                                capture_output=True,
                                text=True)
        if output.returncode == 0:
            text.insert(tk.END,
                        "{}:Monkey日志保存成功! 路径：sdcard/monkey/monkey_log.txt\n".format(datetime.datetime.now()))
            text.insert(tk.END, "{}:可拔掉数据线\n".format(datetime.datetime.now()))
        else:
            text.insert(tk.END, "{}:Monkey日志保存失败!!!\n".format(datetime.datetime.now()))

    def check_logcat():
        output = subprocess.run("adb -s {} shell ls /sdcard/monkey/logcat.txt".format(selected_sn), shell=True,
                                capture_output=True,
                                text=True)
        if output.returncode == 0:
            text.insert(tk.END,
                        "{}:logcat日志保存成功! 路径：sdcard/monkey/logcat.txt\n".format(datetime.datetime.now()))
        else:
            text.insert(tk.END, "{}:logcat日志保存失败!!!\n".format(datetime.datetime.now()))

    def check_logcat_and_monkey_log():
        check_logcat()
        check_monkey_log()

    def get_monkey_pid(selected_sn):
        # 使用adb命令获取进程列表
        adb_command = 'adb -s {} shell ps | findstr "com.android.commands.monkey" '.format(selected_sn)
        try:
            output = subprocess.check_output(adb_command, shell=True, text=True)
            lines = output.strip().split('\n')
            for line in lines:
                if "com.android.commands.monkey" in line:
                    pid = line.split()[1]  # 获取 PID
                    return pid
            return None
        except subprocess.CalledProcessError:
            return None

    def run_white_monkey():
        touch, motion, trackball, nav, majornav, syskeys, appswitch, anyevent, pinchzoom, rotation, number, velocity, crashes, timeout, exceptions, native, option = get_settings()
        monkey_white_cmd = f'adb -s {selected_sn} shell "cd sdcard; monkey --pkg-whitelist-file /sdcard/whitelist.txt --throttle {velocity}{crashes}{timeout}{exceptions}{native} --pct-touch {touch} --pct-motion {motion} --pct-trackball {trackball} --pct-nav {nav} --pct-majornav {majornav} --pct-syskeys {syskeys} --pct-appswitch {appswitch} --pct-anyevent {anyevent} --pct-pinchzoom {pinchzoom} --pct-rotation {rotation}{option} {number} >monkey/monkey_log.txt"'
        pid_container = {}  # 用于存储PID

        def get_pid_and_store(selected_sn):
            """
            循环尝试获取PID，直到获取成功或超时。
            """
            time.sleep(1)
            start_time = time.time()
            while time.time() - start_time < 10:  # 尝试10秒
                pid = get_monkey_pid(selected_sn)
                if pid:
                    pid_container['pid'] = pid
                    text.insert(tk.END, "{}:Monkey PID: {}\n".format(datetime.datetime.now(), pid))
                    return
                time.sleep(0.5)  # 暂停0.5秒后重试
            print("获取Monkey PID超时")

        pid_thread = threading.Thread(target=get_pid_and_store, args=(selected_sn,))
        pid_thread.start()
        execute_monkey_command(monkey_white_cmd)
        # text.insert(tk.END, "{}:Monkey执行命令{}\n".format(datetime.datetime.now(), monkey_white_cmd))

    def run_black_monkey():
        touch, motion, trackball, nav, majornav, syskeys, appswitch, anyevent, pinchzoom, rotation, number, velocity, crashes, timeout, exceptions, native, option = get_settings()
        monkey_black_cmd = f'adb -s {selected_sn} shell "cd sdcard; monkey --pkg-blacklist-file /sdcard/blacklist.txt --throttle {velocity}{crashes}{timeout}{exceptions}{native} --pct-touch {touch} --pct-motion {motion} --pct-trackball {trackball} --pct-nav {nav} --pct-majornav {majornav} --pct-syskeys {syskeys} --pct-appswitch {appswitch} --pct-anyevent {anyevent} --pct-pinchzoom {pinchzoom} --pct-rotation {rotation}{option} {number} >monkey/monkey_log.txt"'
        pid_container = {}  # 用于存储PID

        def get_pid_and_store(selected_sn):
            """
            循环尝试获取PID，直到获取成功或超时。
            """
            time.sleep(1)
            start_time = time.time()
            while time.time() - start_time < 10:  # 尝试10秒
                pid = get_monkey_pid(selected_sn)
                if pid:
                    pid_container['pid'] = pid
                    text.insert(tk.END, "{}:Monkey PID: {}\n".format(datetime.datetime.now(), pid))
                    return
                time.sleep(0.5)  # 暂停0.5秒后重试
            print("获取Monkey PID超时")

        pid_thread = threading.Thread(target=get_pid_and_store, args=(selected_sn,))
        pid_thread.start()
        execute_monkey_command(monkey_black_cmd)
        # text.insert(tk.END, "{}:Monkey执行命令{}\n".format(datetime.datetime.now(), monkey_black_cmd))

    def execute_monkey_command(monkey_command):
        text.insert(tk.END, "{}:开始执行Monkey测试\n".format(datetime.datetime.now()))
        output = subprocess.check_output(monkey_command, shell=True, stderr=subprocess.STDOUT)


    def create_blacklist():
        if not listbox1.curselection():
            tkinter.messagebox.showerror("错误", "请先选择要添加到黑名单的包名")
            return
        touch, motion, trackball, nav, majornav, syskeys, appswitch, anyevent, pinchzoom, rotation, number, velocity, crashes, timeout, exceptions, native, option = get_settings()
        # 将每个值转换为整型
        int_touch = int(touch)
        int_motion = int(motion)
        int_trackball = int(trackball)
        int_nav = int(nav)
        int_majornav = int(majornav)
        int_syskeys = int(syskeys)
        int_appswitch = int(appswitch)
        int_anyevent = int(anyevent)
        int_pinchzoom = int(pinchzoom)
        int_rotation = int(rotation)

        # 计算总和
        total = int_touch + int_motion + int_trackball + int_nav + int_majornav + int_syskeys + int_appswitch + int_anyevent + int_pinchzoom + int_rotation
        if total != 100:
            tkinter.messagebox.showerror("错误", "请确保所有事件占比加起来为100%")
            return
        text.delete('1.0', tk.END)
        check_monkey()
        subprocess.call("adb -s {} logcat -G 64m".format(selected_sn), shell=True)
        text.insert(tk.END, "{}:已增加logcat缓存\n".format(datetime.datetime.now()))
        selected_packages = listbox1.selection_get().split("\n")
        with open("blacklist.txt", "w") as file:
            for package in selected_packages:
                file.write(package + "\n")
        text.insert(tk.END, "{}:已将{}加入到blacklist.txt文件中\n".format(datetime.datetime.now(), selected_packages))
        logcat_thread = threading.Thread(target=run_logcat)
        logcat_thread.start()
        subprocess.run("adb -s {} push blacklist.txt sdcard".format(selected_sn), shell=True)
        text.insert(tk.END, "{}:导入blacklist.txt\n".format(datetime.datetime.now()))
        monkey_thread = threading.Thread(target=run_black_monkey)
        monkey_thread.start()
        offline_window.after(2000, check_logcat_and_monkey_log)  # 2秒后检查日志

    def create_whitelist():
        if not listbox1.curselection():
            tkinter.messagebox.showerror("错误", "请先选择要添加到白名单的包名")
            return
        touch, motion, trackball, nav, majornav, syskeys, appswitch, anyevent, pinchzoom, rotation, number, velocity, crashes, timeout, exceptions, native, option = get_settings()
        # 将每个值转换为整型
        int_touch = int(touch)
        int_motion = int(motion)
        int_trackball = int(trackball)
        int_nav = int(nav)
        int_majornav = int(majornav)
        int_syskeys = int(syskeys)
        int_appswitch = int(appswitch)
        int_anyevent = int(anyevent)
        int_pinchzoom = int(pinchzoom)
        int_rotation = int(rotation)

        # 计算总和
        total = int_touch + int_motion + int_trackball + int_nav + int_majornav + int_syskeys + int_appswitch + int_anyevent + int_pinchzoom + int_rotation
        if total != 100:
            tkinter.messagebox.showerror("错误", "请确保所有事件占比加起来为100%")
            return
        text.delete('1.0', tk.END)
        check_monkey()
        subprocess.call("adb -s {} logcat -G 64m".format(selected_sn), shell=True)
        text.insert(tk.END, "{}:已增加logcat缓存\n".format(datetime.datetime.now()))
        selected_packages = listbox1.selection_get().split("\n")
        with open("whitelist.txt", "w") as file:
            for package in selected_packages:
                file.write(package + "\n")
        text.insert(tk.END, "{}:已将{}加入到whitelist.txt文件中\n".format(datetime.datetime.now(), selected_packages))
        logcat_thread = threading.Thread(target=run_logcat)
        logcat_thread.start()
        subprocess.run("adb -s {} push whitelist.txt sdcard".format(selected_sn), shell=True)
        text.insert(tk.END, "{}:导入whitelist.txt\n".format(datetime.datetime.now()))
        monkey_thread = threading.Thread(target=run_white_monkey)
        monkey_thread.start()
        offline_window.after(2000, check_logcat_and_monkey_log)  # 2秒后检查日志

    def disable_drag(event):
        event.widget.focus_set()
        return "break"

    def bind_entry(entry):
        entry.bind("<Button-1>", disable_drag)

    def validate_input(new_value):
        if new_value == "0" or (new_value.isdigit() and len(new_value) <= 2):
            return True
        else:
            return False
    def validate2_input(new_value2):
        if new_value2.isdigit():
            return True
        else:
            return False

    def copy_text(event=None):
        try:
            selected_text = text.get("sel.first", "sel.last")
            root = tk.Tk()
            root.withdraw()
            root.clipboard_clear()
            root.clipboard_append(selected_text)
            root.update()  # 更新剪贴板
        except tk.TclError:
            pass  # 如果没有选中的文本，忽略错误

    validate = offline_window.register(validate_input)
    validate2 = offline_window.register(validate2_input)

    listbox1.bind("<<ListboxSelect>>", on_select)

    if not os.path.exists('user_settings_offline.json'):
        user_settings = {
            'input1': 50,
            'input2': 10,
            'input3': 5,
            'input4': 5,
            'input5': 5,
            'input6': 5,
            'input7': 5,
            'input8': 5,
            'input9': 5,
            'input10': 5,
            'input11': 1000,
            'input12': 200,
            'input13': 60,
            'dropdown': '详细',
            'checkbox1': False,
            'checkbox2': False,
            'checkbox3': False,
            'checkbox4': False
        }
    else:
        with open('user_settings_offline.json', 'r') as file:
            user_settings = json.load(file)


    black_button = tk.Button(offline_window, text="黑名单测试", command=create_blacklist)
    black_button.place(x=200, y=370,anchor="center")

    white_button = tk.Button(offline_window, text="白名单测试", command=create_whitelist)
    white_button.place(x=600, y=370, anchor="center")

    label1 = tk.Label(offline_window, text="请选择要测试的包:", font=("Arial", 15))
    label1.place(x=10, y=0)

    label2 = tk.Label(offline_window, text="日志输出等级:", font=("Arial", 10))
    label2.place(x=600, y=30)
    combo_box = ttk.Combobox(offline_window, values=["简略", "一般", "详细"], width=5, state="readonly")
    combo_box.set(user_settings.get('dropdown', '详细'))
    combo_box.place(x=700, y=30)

    label6 = tk.Label(offline_window, text="日志抓取时长(秒):", font=("Arial", 10))
    label6.place(x=600, y=80)
    search_logcat_time = tk.Entry(offline_window, validate="key", validatecommand=(validate2, "%P"))
    search_logcat_time.insert(0, str(user_settings['input13']))
    search_logcat_time.place(x=600, y=100, width=100)

    label3 = tk.Label(offline_window, text="Monkey执行次数:", font=("Arial", 10))
    label3.place(x=600, y=120)
    search_frequency = tk.Entry(offline_window, validate="key", validatecommand=(validate2, "%P"))
    search_frequency.insert(0, str(user_settings['input11']))
    search_frequency.place(x=600, y=140, width=100)

    label4 = tk.Label(offline_window, text="延迟时间:", font=("Arial", 10))
    label4.place(x=600, y=160)
    search_time = tk.Entry(offline_window, validate="key", validatecommand=(validate2, "%P"))
    search_time.insert(0, str(user_settings['input12']))
    search_time.place(x=600, y=180, width=100)

    label5 = tk.Label(offline_window, text="设置事件占比:", font=("Arial", 14))
    label5.place(x=400, y=30)

    label_touch = tk.Label(offline_window, text="触摸事件:", font=("Arial", 10))
    label_touch.place(x=400, y=60)
    search_touch = tk.Entry(offline_window, validate="key", validatecommand=(validate, "%P"))
    search_touch.insert(0, str(user_settings['input1']))
    search_touch.place(x=500, y=60, width=50)

    label_motion = tk.Label(offline_window, text="动作事件:", font=("Arial", 10))
    label_motion.place(x=400, y=90)
    search_motion = tk.Entry(offline_window, validate="key", validatecommand=(validate, "%P"))
    search_motion.insert(0, str(user_settings['input2']))
    search_motion.place(x=500, y=90, width=50)

    label_trackball = tk.Label(offline_window, text="轨迹球事件:", font=("Arial", 10))
    label_trackball.place(x=400, y=120)
    search_trackball = tk.Entry(offline_window, validate="key", validatecommand=(validate, "%P"))
    search_trackball.insert(0, str(user_settings['input3']))
    search_trackball.place(x=500, y=120, width=50)

    label_nav = tk.Label(offline_window, text="导航事件:", font=("Arial", 10))
    label_nav.place(x=400, y=150)
    search_nav = tk.Entry(offline_window, validate="key", validatecommand=(validate, "%P"))
    search_nav.insert(0, str(user_settings['input4']))
    search_nav.place(x=500, y=150, width=50)

    label_majornav = tk.Label(offline_window, text="主导航事件:", font=("Arial", 10))
    label_majornav.place(x=400, y=180)
    search_majornav = tk.Entry(offline_window, validate="key", validatecommand=(validate, "%P"))
    search_majornav.insert(0, str(user_settings['input5']))
    search_majornav.place(x=500, y=180, width=50)

    label_syskeys = tk.Label(offline_window, text="系统按键事件:", font=("Arial", 10))
    label_syskeys.place(x=400, y=210)
    search_syskeys = tk.Entry(offline_window, validate="key", validatecommand=(validate, "%P"))
    search_syskeys.insert(0, str(user_settings['input6']))
    search_syskeys.place(x=500, y=210, width=50)

    label_appswitch = tk.Label(offline_window, text="应用切换事件:", font=("Arial", 10))
    label_appswitch.place(x=400, y=240)
    search_appswitch = tk.Entry(offline_window, validate="key", validatecommand=(validate, "%P"))
    search_appswitch.insert(0, str(user_settings['input7']))
    search_appswitch.place(x=500, y=240, width=50)

    label_anyevent = tk.Label(offline_window, text="任意事件:", font=("Arial", 10))
    label_anyevent.place(x=400, y=270)
    search_anyevent = tk.Entry(offline_window, validate="key", validatecommand=(validate, "%P"))
    search_anyevent.insert(0, str(user_settings['input8']))
    search_anyevent.place(x=500, y=270, width=50)

    label_pinchzoom = tk.Label(offline_window, text="捏合缩放事件:", font=("Arial", 10))
    label_pinchzoom.place(x=400, y=300)
    search_pinchzoom = tk.Entry(offline_window, validate="key", validatecommand=(validate, "%P"))
    search_pinchzoom.insert(0, str(user_settings['input9']))
    search_pinchzoom.place(x=500, y=300, width=50)

    label_rotation = tk.Label(offline_window, text="旋转事件:", font=("Arial", 10))
    label_rotation.place(x=400, y=330)
    search_rotation = tk.Entry(offline_window, validate="key", validatecommand=(validate, "%P"))
    search_rotation.insert(0, str(user_settings['input10']))
    search_rotation.place(x=500, y=330, width=50)

    label6 = tk.Label(offline_window, text="调试:", font=("Arial", 14))
    label6.place(x=600, y=210)

    check_crashes_var = tk.IntVar()
    checkbox_crashes = tk.Checkbutton(offline_window, text="忽略应用程序崩溃", variable=check_crashes_var)
    check_crashes_var.set(user_settings['checkbox1'])
    checkbox_crashes.place(x=600, y=240)

    check_timeout_var = tk.IntVar()
    checkbox_timeout = tk.Checkbutton(offline_window, text="忽略超时", variable=check_timeout_var)
    check_timeout_var.set(user_settings['checkbox2'])
    checkbox_timeout.place(x=600, y=270)

    check_exceptions_var = tk.IntVar()
    checkbox_exceptions = tk.Checkbutton(offline_window, text="忽略安全异常", variable=check_exceptions_var)
    check_exceptions_var.set(user_settings['checkbox3'])
    checkbox_exceptions.place(x=600, y=300)

    check_native_crashes_var = tk.IntVar()
    checkbox_native_crashes = tk.Checkbutton(offline_window, text="忽略本地代码崩溃崩溃",
                                             variable=check_native_crashes_var)
    check_native_crashes_var.set(user_settings['checkbox4'])
    checkbox_native_crashes.place(x=600, y=330)

    # 禁用多个输入框的双击和长按拖动事件
    for entry in [search_touch, search_motion, search_trackball, search_nav, search_majornav, search_syskeys, search_appswitch, search_anyevent, search_pinchzoom, search_rotation, search_frequency, search_time, search_logcat_time]:
        bind_entry(entry)

    scrollbar2 = tk.Scrollbar(offline_window)
    scrollbar2.place(x=700, y=395, height=15)
    text = tk.Text(offline_window, height=15, width=113, yscrollcommand=scrollbar2.set)
    text.place(x=1,y=395)
    text.insert(tk.END, "")
    # 将Scrollbar控件与Text控件绑定
    scrollbar.config(command=text.yview)

    offline_window.bind('<Control-c>', copy_text)

    # 添加右键菜单
    def show_context_menu(event):
        context_menu.post(event.x_root, event.y_root)

    context_menu = tk.Menu(offline_window, tearoff=0)
    context_menu.add_command(label="复制", command=copy_text)

    text.bind('<Control-c>', copy_text)
    text.bind("<Button-3>", show_context_menu)  # 右键菜单

    def get_settings():
        touch = search_touch.get()
        motion = search_motion.get()
        trackball = search_trackball.get()
        nav = search_nav.get()
        majornav = search_majornav.get()
        syskeys = search_syskeys.get()
        appswitch = search_appswitch.get()
        anyevent = search_anyevent.get()
        pinchzoom = search_pinchzoom.get()
        rotation = search_rotation.get()
        number = search_frequency.get()
        velocity = search_time.get()

        if check_crashes_var.get() == 1:
            crashes = " --ignore-crashes"
        else:
            crashes = ""
        if check_timeout_var.get() == 1:
            timeout = " --ignore-timeouts"
        else:
            timeout = ""
        if check_exceptions_var.get() == 1:
            exceptions = " --ignore-security-exceptions"
        else:
            exceptions = ""
        if check_native_crashes_var.get() == 1:
            native = " --ignore-native-crashes"
        else:
            native = ""

        selected_option = combo_box.get()
        if selected_option == "简略":
            option = " -v"
        if selected_option == "一般":
            option = " -v -v"
        if selected_option == "详细":
            option = " -v -v -v"

        return touch, motion, trackball, nav, majornav, syskeys, appswitch, anyevent, pinchzoom, rotation, number, velocity, crashes, timeout, exceptions, native, option
    def save_settings():
        user_settings['input1'] = int(search_touch.get())
        user_settings['input2'] = int(search_motion.get())
        user_settings['input3'] = int(search_trackball.get())
        user_settings['input4'] = int(search_nav.get())
        user_settings['input5'] = int(search_majornav.get())
        user_settings['input6'] = int(search_syskeys.get())
        user_settings['input7'] = int(search_appswitch.get())
        user_settings['input8'] = int(search_anyevent.get())
        user_settings['input9'] = int(search_pinchzoom.get())
        user_settings['input10'] = int(search_rotation.get())
        user_settings['input11'] = int(search_frequency.get())
        user_settings['input12'] = int(search_time.get())
        user_settings['input13'] = int(search_logcat_time.get())
        user_settings['dropdown'] = combo_box.get()
        user_settings['checkbox1'] = check_crashes_var.get()
        user_settings['checkbox2'] = check_timeout_var.get()
        user_settings['checkbox3'] = check_exceptions_var.get()
        user_settings['checkbox4'] = check_native_crashes_var.get()

        with open('user_settings_offline.json', 'w') as file:
            json.dump(user_settings, file)

    def on_closing():
        save_settings()
        offline_window.destroy()

    def on_combobox_select(event):
        # 保存当前选中的包名索引
        selected_indices = listbox1.curselection()
        # 执行下拉框选择操作
        selected_option = combo_box.get()
        # 恢复之前选中的包名
        for index in selected_indices:
            listbox1.selection_set(index)

    def on_key_press(event):
        return 'break'

    text.bind("<Key>", on_key_press)
    combo_box.bind("<<ComboboxSelected>>", on_combobox_select)

    offline_window.protocol("WM_DELETE_WINDOW", on_closing)
    opened_windows[selected_sn] = offline_window
    return offline_window

    offline_window.mainloop()

# 获取手机中所有软件包名
def get_package_names(selected_sn):
    package_names = []
    adb_command = "adb -s {} shell pm list packages".format(selected_sn)
    result = subprocess.Popen(adb_command, shell=True, stdout=subprocess.PIPE).stdout.read().decode('utf-8')
    for line in result.splitlines():
        package_names.append(line.split(":")[-1])
    return package_names