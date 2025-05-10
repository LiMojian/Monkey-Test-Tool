import tkinter as tk
import tkinter.messagebox
from secondary_window import open_secondary_window
from tkinter import PhotoImage
import sqlite3  # 新增数据库导入
from tkinter import ttk, messagebox
import threading
import time
import random
from packaging import version
import socket
from datetime import datetime
import mysql.connector


class OTAManager:
    def __init__(self, root):
        self.root = root
        self.current_version = "1.0.0"
        self.latest_version = "1.2.0"

        # 检查更新按钮
        self.check_update_btn = ttk.Button(root, text="检查更新", command=self.check_for_updates)
        self.check_update_btn.pack(side=tk.TOP, fill=tk.X, padx=80)
        self.check_update_btn.place(relx=0.5, rely=0.5, anchor="center")

        # 状态标签
        self.status_label = tk.Label(root, text="")
        self.status_label.place(relx=0.5, rely=0.6, anchor="center")

    def check_for_updates(self):
        """模拟检查更新"""
        self.status_label.config(text="正在检查更新...")

        # 模拟网络请求
        threading.Thread(target=self._simulate_check).start()

    def _simulate_check(self):
        """模拟网络检查"""
        time.sleep(2)  # 模拟网络延迟

        if self.current_version != self.latest_version:
            self.root.after(0, self.show_update_available)
        else:
            self.root.after(0, lambda: self.status_label.config(text="已是最新版本"))

    def show_update_available(self):
        """显示更新可用对话框"""
        self.update_window = tk.Toplevel(self.root)
        self.update_window.title("软件更新")
        self.update_window.geometry("500x400")

        # 标题
        tk.Label(self.update_window, text="新版本可用!", font=("Arial", 14, "bold")).pack(pady=10)

        # 版本信息
        versions_frame = tk.Frame(self.update_window)
        versions_frame.pack(pady=10)

        tk.Label(versions_frame, text=f"当前版本: {self.current_version}").pack(side="left", padx=20)
        tk.Label(versions_frame, text="→", font=("Arial", 12)).pack(side="left", padx=10)
        tk.Label(versions_frame, text=f"最新版本: {self.latest_version}", fg="green").pack(side="left", padx=20)

        # 更新说明
        notes_frame = tk.LabelFrame(self.update_window, text="更新内容")
        notes_frame.pack(pady=10, padx=20, fill="both", expand=True)

        notes_text = tk.Text(notes_frame, height=10, wrap="word")
        notes_text.pack(fill="both", expand=True, padx=5, pady=5)
        notes_text.insert("1.0", "1. 新增了用户反馈功能\n2. 优化了性能表现\n3. 修复了若干已知问题\n4. 改进了用户界面")
        notes_text.config(state="disabled")

        # 按钮
        btn_frame = tk.Frame(self.update_window)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="立即更新", command=self.start_update).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="稍后提醒", command=self.update_window.destroy).pack(side="left", padx=10)

    def start_update(self):
        """开始更新流程"""
        self.update_window.destroy()

        # 创建进度窗口
        self.progress_window = tk.Toplevel(self.root)
        self.progress_window.title("软件更新")
        self.progress_window.geometry("400x250")

        # 标题
        tk.Label(self.progress_window, text="正在下载更新...", font=("Arial", 12)).pack(pady=10)

        # 进度条
        self.progress = ttk.Progressbar(self.progress_window, orient="horizontal", length=300, mode="determinate")
        self.progress.pack(pady=10)

        # 百分比
        self.percent_label = tk.Label(self.progress_window, text="0%")
        self.percent_label.pack()

        # 详情
        self.detail_label = tk.Label(self.progress_window, text="准备下载...")
        self.detail_label.pack(pady=10)

        # 取消按钮
        ttk.Button(self.progress_window, text="取消", command=self.cancel_update).pack(pady=10)

        # 模拟下载线程
        threading.Thread(target=self._simulate_download).start()

    def _simulate_download(self):
        """模拟下载过程"""
        for i in range(101):
            if self.cancelled:
                break

            time.sleep(0.05)  # 模拟下载延迟
            progress = i

            # 更新UI
            #self.root.after(0, lambda p=progress: self.progress["value"] = p)
            self.root.after(0, lambda p=progress: self.percent_label.config(text=f"{p}%"))

            # 更新状态信息
            if i < 30:
                status = "正在下载更新文件..."
            elif i < 70:
                status = "正在验证文件完整性..."
            else:
                status = "准备安装..."

            self.root.after(0, lambda s=status: self.detail_label.config(text=s))

        if not self.cancelled:
            self.root.after(0, self.complete_update)

    def cancel_update(self):
        """取消更新"""
        self.cancelled = True
        self.progress_window.destroy()
        messagebox.showinfo("更新已取消", "软件更新已被取消")

    def complete_update(self):
        """完成更新"""
        self.progress_window.destroy()
        messagebox.showinfo("更新完成", "软件已成功更新到最新版本!")
        self.current_version = self.latest_version
        self.status_label.config(text=f"当前版本: {self.current_version}")

class MyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("我的应用程序")

        # 当前版本号 (从文件中读取，或者硬编码)
        self.current_version = self.get_current_version()

        # 显示当前版本信息的标签
        self.version_label = tk.Label(root, text=f"当前版本: {self.current_version}")
        self.version_label.pack(pady=10)

        # 版本检测结果显示区域
        self.update_status_label = tk.Label(root, text="")
        self.update_status_label.pack(pady=5)

        # 版本检测按钮
        self.check_button = tk.Button(root, text="检查更新", command=self.check_for_update)
        self.check_button.pack(pady=20)

    def get_current_version(self):
        """从文件中读取当前版本号，如果文件不存在，则返回一个默认值"""
        try:
            with open("version.txt", "r") as f:
                return f.read().strip()
        except FileNotFoundError:
            return "1.0"  # 默认版本号

    def check_for_update(self):
        try:
            # 从服务器获取最新版本号
            online_version = urllib.request.urlopen("http://yourserver.com/version.txt", timeout=5).read().decode('utf-8').strip()

            if online_version > self.current_version:
                self.update_status_label.config(text="发现新版本！")
                if messagebox.askyesno("更新", "发现新版本，是否更新？"):
                    self.download_and_update()
            else:
                self.update_status_label.config(text="当前已是最新版本。")

        except Exception as e:
            self.update_status_label.config(text=f"检查更新出错: {e}")
            messagebox.showerror("错误", f"检查更新出错: {e}")

    def download_and_update(self):
        try:
            # 下载新的 EXE 文件
            new_exe_path = "your_app_new.exe"
            urllib.request.urlretrieve("http://yourserver.com/your_app.exe", new_exe_path)

            # 替换旧的 EXE 文件
            self.replace_exe(new_exe_path)

        except Exception as e:
            messagebox.showerror("错误", f"更新出错: {e}")

    def replace_exe(self, new_exe_path):
        """替换当前 EXE 文件，需要管理员权限"""
        try:
            # 获取当前 EXE 文件的路径
            current_exe_path = sys.executable

            # 创建一个批处理文件，用于替换 EXE 文件
            # 因为直接替换正在运行的 EXE 文件可能会失败
            batch_script = """  
            @echo off  
            taskkill /f /im "{}"  
            timeout /t 2 /nobreak > nul  
            move /y "{}" "{}"  
            start "" "{}"  
            del "%~f0"  
            """.format(os.path.basename(current_exe_path),
                       new_exe_path,
                       current_exe_path,
                       current_exe_path)

            # 将批处理脚本保存到临时文件
            batch_file_path = "update.bat"
            with open(batch_file_path, "w") as f:
                f.write(batch_script)

            # 使用管理员权限运行批处理文件
            subprocess.Popen(["runas", "/user:administrator", batch_file_path])  # 需要管理员密码
            #subprocess.Popen([batch_file_path], shell=True)  # 如果不需要管理员权限，可以直接运行

            # 退出当前程序
            self.root.destroy()  # 关闭 Tkinter 窗口
            sys.exit()


        except Exception as e:
            messagebox.showerror("错误", f"替换 EXE 文件出错: {e}")

    def restart_program(self):  #  不再需要
        pass

def resize(event):
    label.config(width=event.width)

# 获取输入框字符串
def get_input():
    input_text = input_box.get()
    return input_text

# 验证输入的密码是否在数据库中
def get_local_ip():
    """
    获取本机局域网IP地址，非127.0.0.1
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = None
    finally:
        s.close()
    return ip

def validate_password(input_password):
    """验证密码是否存在且未被使用（满足条件）"""
    local_ip = get_local_ip()
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        connection = mysql.connector.connect(
            host='192.168.22.196',
            port=3307,
            user='root',
            password='54665426',
            database='kingdatabase',
            charset='utf8mb4'
        )
        with connection.cursor() as cursor:
            # 查询满足条件的密码（condi=0或ip一致）
            query = """
            SELECT id FROM passwords 
            WHERE password=%s AND (condi=0 OR ip=%s)
            LIMIT 1
            """
            cursor.execute(query, (input_password, local_ip))
            result = cursor.fetchone()

            if result:
                password_id = result[0]
                # 更新这行记录：condi=1，ip=本机IP，use_at=当前时间
                update_query = """
                UPDATE passwords
                SET condi=1, ip=%s, use_at=%s
                WHERE id=%s
                """
                cursor.execute(update_query, (local_ip, current_time, password_id))
                connection.commit()
                return True
            else:
                return False
    except mysql.connector.Error as err:
        messagebox.showerror("数据库错误", f"{err}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()

def check_and_open_secondary_window():
    input_text = get_input()
    if validate_password(input_text):  # 改为数据库验证
        root.withdraw()  # 隐藏主窗口
        open_secondary_window(root)
    else:
        messagebox.showerror("密码错误", "请向开发者询问正确密码后输入!")

# 点击复选框时切换密钥显示状态
def toggle_password_visibility():
    if show_password_var.get():  # 如果复选框被选中
        input_box.config(show="")  # 显示明文密码
    else:
        input_box.config(show="*")  # 隐藏密码

def center_window(window):
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry('{}x{}+{}+{}'.format(width, height, x, y))

# 鼠标悬停提示
class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None

    def show_tip(self):
        if self.tip_window or not self.text:
            return
        x, y = self.widget.winfo_pointerxy()
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x + 10, y + 10))

        label = tk.Label(tw, text=self.text, background="#ffffe0", relief="solid", borderwidth=1)
        label.pack(ipadx=1)

    def hide_tip(self):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

def create_tooltip(widget, text):
    tooltip = Tooltip(widget, text)
    widget.bind("<Enter>", lambda e: tooltip.show_tip())
    widget.bind("<Leave>", lambda e: tooltip.hide_tip())

# 应用设置图标
def set_icon():
    icon = PhotoImage(file='monkey.png')
    root.iconphoto(False, icon)

# 主窗口
root = tk.Tk()
root.after(0, set_icon)  # 100毫秒后设置图标
root.title("King")

# 设置窗口信息
root.geometry("400x300")
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

x = (screen_width - 400) // 2
y = (screen_height - 300) // 2

ota = OTAManager(root)

# 设置窗口位置
root.geometry("+{}+{}".format(x, y))

label1 = tk.Label(root, text="欢迎使用Monkey测试工具！", font=("Arial", 20), bg="lightblue")
label1.pack(side=tk.TOP, fill=tk.X, padx=10)

label2 = tk.Label(root, text="请输入密钥:", font=("Arial", 15))
label2.place(relx=0.18, rely=0.2, anchor="center")

button = tk.Button(root, text="检测USB", command=check_and_open_secondary_window, bg="lightblue")
button.pack(side=tk.TOP, fill=tk.X, padx=80)
button.place(relx=0.5, rely=0.8, anchor="center")

# 输入框
input_box = tk.Entry(root, show="*")
input_box.place(relx=0.5, rely=0.2, anchor="center")

# 添加复选框用于显示密钥
show_password_var = tk.BooleanVar()  # 复选框变量
show_password_checkbox = tk.Checkbutton(root, text="显示密钥", variable=show_password_var, command=toggle_password_visibility)
show_password_checkbox.place(relx=0.5, rely=0.3, anchor="center")

# 鼠标悬停提示
label = tk.Label(root, text="密钥提示")
label.place(relx=0.8, rely=0.2, anchor="center")
create_tooltip(label, "请找开发者寻求密钥")

# 创建一个标签，用于显示版权信息
copyright_label = tk.Label(root, text="© 2025 Mojian Li. All rights reserved.", fg="gray")
copyright_label.pack(side="bottom")

def on_main_window_close():
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_main_window_close)

root.mainloop()