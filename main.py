import sys
import os
import json
import random
import math
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QMenu, QAction, QSystemTrayIcon,
    QInputDialog, QMessageBox, QVBoxLayout, QHBoxLayout, QPushButton,
    QDialog, QListWidget, QDialogButtonBox
)
from PyQt5.QtGui import QPixmap, QPainter, QBitmap, QIcon, QFont, QColor, QFontMetrics
from PyQt5.QtCore import (
    Qt, QTimer, QPoint, QSize, QRect, QPropertyAnimation, QEasingCurve,
    pyqtProperty
)

# ======================== 路径配置 ========================
# 兼容 PyInstaller 打包后的 exe 模式（sys.frozen=True 时用 exe 所在目录）
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, "assets", "images")
AUDIO_DIR = os.path.join(BASE_DIR, "assets", "audio")
DATA_DIR = os.path.join(BASE_DIR, "data")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
REMINDERS_FILE = os.path.join(DATA_DIR, "reminders.json")

os.makedirs(DATA_DIR, exist_ok=True)


# ======================== 台词截断工具 ========================
# 气泡最大宽度：放宽到 380px，确保大部分常见台词可以 1~2 行完整显示（少"..."截断）
BUBBLE_MAX_WIDTH = 380

def _limit_lines(text, max_lines=2, max_width=BUBBLE_MAX_WIDTH):
    """将长台词限制为最多 max_lines 行，超过用省略号结尾；加宽后完整显示率更高"""
    font = QFont("Microsoft YaHei", 10)
    fm = QFontMetrics(font)
    words = list(text)
    lines = []
    cur = ""
    for ch in words:
        test = cur + ch
        if fm.width(test) > max_width:
            lines.append(cur)
            cur = ch
            if len(lines) >= max_lines:
                # 已满 max_lines 行：在最后一行末尾加 "..."（若空间够）
                last = lines[-1]
                suffix = "..."
                while last and fm.width(last + suffix) > max_width and len(last) > 0:
                    last = last[:-1]
                lines[-1] = last + suffix
                cur = ""
                break
        else:
            cur = test
    if cur and len(lines) < max_lines:
        lines.append(cur)
    elif cur and len(lines) >= max_lines:
        # 还有剩余字符但已到行上限，在最后一行追加 "..."
        last = lines[-1]
        suffix = "..."
        while last and fm.width(last + suffix) > max_width and len(last) > 0:
            last = last[:-1]
        lines[-1] = last + suffix
    return "\n".join(lines)


# ======================== 台词库 ========================
XIAR_QUOTES = [
    "虾哥，别家比咱们还穷，这饭不好讨啊。",
    "头好痛…… 我不是还在熬夜刷视频吗？怎么一转眼就换了个身子，这是哪儿？",
    "原主居然被欺负到丢了性命？既然我占了这具身体，从前的账，我替你一笔一笔讨回来。",
    "既来之，则安之。烂摊子再乱，慢慢收拾总能翻盘，活人总不能被困境困住。",
    "以前我只是个普通人，如今重活一世，往后我的人生，由我自己说了算。",
    "前世庸庸碌碌浑浑噩噩，这一世，我绝不会再委屈自己。",
    "穿越已成定局，抱怨无用，当下最要紧的是摸清处境，保全自身。",
    "世道混乱、人心险恶没关系，我手握未来阅历，前路再难，也能踏出一条生路。",
    "不必惊慌，我来自后世，很多你们想不通的难题，于我而言只是常识。",
    "前世吃过的苦、踩过的坑，今生我全部避开，只奔着安稳与前程而去。",
    "好不容易重活一次，不内卷不拼命，吃饱喝足安稳度日，就是最大的福气。",
    "谁爱争前程谁去争，我只想躺平过日子，安稳活到寿终正寝就够了。",
    "叮！人生逆袭系统绑定成功，新手大礼包已发放，开启新手任务即可领取奖励。",
    "完成任务就能兑换物资、学识、医术武学？有这系统，翻身简直易如反掌。",
    "系统，兑换强身丹药！眼下强敌环伺，我必须尽快变强自保。",
    "我记得三年后这里会发生灾祸，提前做好准备，就能躲过一劫。",
    "此人日后会身居高位，现在多结一份善缘，将来便是我的靠山。",
    "我清楚未来数年时局走向，只要顺势而为，财富、权势唾手可得。",
    "别人看不清局势，我却知晓结局，这便是我最大的依仗。",
    "脑海里这片独立空间，可存万物、保鲜永久，往后不愁粮食与物资了。",
    "空间泉水能疗伤健体，有此物在，重伤顽疾都不必畏惧。",
    "悄悄把物资存入空间，乱世之中，手握粮草，就握住了底气。",
    "脑海中凭空多出全套医书典籍，寻常疑难杂症，我抬手便可医治。",
    "现代数理化知识刻入脑海，改良农具、搭建工事，古人不懂的，我随手就能造出。",
    "无数兵家谋略熟记于心，战场博弈，我一眼便能看破敌军计谋。",
    "你们嘲笑我一无所有，殊不知我手握旁人求不来的机缘，很快你们就只能仰望我。",
    "之前你们百般轻视欺辱，如今我凭本事崛起，往后再想攀附，已经晚了。",
    "别用你的眼界定义我的未来，你看不到我的底牌，自然看不懂我的前路。",
    "靠旁人庇护终究虚幻，我自有金手指傍身，不必依附任何人。",
    "一朝穿越凡尘，幸得天赐机缘，他日乘风而起，俯瞰山河万里。",
    "世人皆求仙问道机缘，而机缘已落我身，苦修精进，必踏巅峰。",
    "乱世浮沉，机缘傍身，定要护亲友安稳，定要活出无上荣光。",
    "一朝穿越，机缘天降，平凡之人，逆天改命。",
    "前世遗憾，今生弥补，金手指在手，万事皆可期。",
    "他人困于当下，我预见未来，步步登顶。",
    "穿越不是终点，金手指，只是传奇的起点。",
]

# ======================== 动态扫描图片（完全不看文件名，只按顺序）========================
# 扫描 assets/images 下所有 .png，按文件名字典序排好后：
#   - key = 文件 stem（不含 .png 后缀，仅用于 pixmaps 字典键，外部不关心）
#   - 顺序 = 列表下标（以后放新图片只要复制到目录就按新顺序扩展，不用改代码）
def _scan_image_order():
    """返回 [(stem, full_path)] 列表，按文件名升序（字典序）——不依赖任何命名规则"""
    if not os.path.isdir(IMG_DIR):
        return []
    files = []
    for fn in os.listdir(IMG_DIR):
        if fn.lower().endswith(".png"):
            stem = os.path.splitext(fn)[0]
            files.append((stem, os.path.join(IMG_DIR, fn)))
    # 只按文件名升序（用户说"所有图片按顺序切换"——不用区分名字含义）
    files.sort(key=lambda t: t[0].lower())
    return files

_SCANNED_FILES = _scan_image_order()

# 姿态列表（顺序严格 = 文件名字典序，从此不再需要手动维护 POSE_GROUPS）
ALL_POSES = [stem for stem, _ in _SCANNED_FILES]

# 姿态名（纯按序号，完全不看名字含义；用户在右键菜单/气泡/日志里只看到"第N个"）
POSE_NAMES = {stem: f"第{i+1}个" for i, (stem, _) in enumerate(_SCANNED_FILES)}

# 姿态文件路径表（用于 _load_images 加载时直接用绝对路径，不管 stem 叫什么）
POSE_PATHS = {stem: path for stem, path in _SCANNED_FILES}

POSE_TOTAL = len(ALL_POSES)


# ======================== 设置管理 ========================
def load_settings():
    default = {
        "position": [200, 400],
        "scale": 0.30,          # 默认大幅缩小，避免原图800x1000过大
        "sit_interval": 30,
        "sit_enabled": True,
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                default.update(data)
        except Exception:
            pass
    return default


def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def load_reminders():
    if os.path.exists(REMINDERS_FILE):
        try:
            with open(REMINDERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_reminders(reminders):
    try:
        with open(REMINDERS_FILE, "w", encoding="utf-8") as f:
            json.dump(reminders, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ======================== 气泡窗口 ========================
class BubbleWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self._text = ""
        self._opacity = 0.0
        # 持有一个隐藏定时器（每次新气泡 showBubble 会先 stop 掉旧的，解决"老singleShot提前关新气泡"bug）
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hideBubble)
        self.hide()

    def setText(self, text):
        # 限制为最多 2 行，超出用 "..." 结尾（与全局 BUBBLE_MAX_WIDTH 保持一致，避免截断过狠）
        self._text = _limit_lines(text, max_lines=2, max_width=BUBBLE_MAX_WIDTH)
        # 计算气泡大小
        font = QFont("Microsoft YaHei", 10)
        fm = QFontMetrics(font)
        lines = self._text.split("\n")
        if not lines:
            lines = [""]
        max_w = 0
        for ln in lines:
            w_line = fm.width(ln)
            if w_line > max_w:
                max_w = w_line
        text_w = max_w + 36           # 加宽 padding，文字不贴边
        text_h = len(lines) * fm.height() + 24
        self.resize(text_w + 20, text_h + 20)
        self.update()

    def paintEvent(self, event):
        if not self._text:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        rect = QRect(10, 5, w - 20, h - 25)
        # 米白暖色调气泡（去黑色）
        bubble_rgb = (255, 250, 238)     # 浅米白背景
        border_rgb = (222, 184, 135)     # 暖棕边框
        text_rgb   = (70, 50, 30)        # 深棕文字
        color  = QColor(*bubble_rgb, int(245 * self._opacity))
        border = QColor(*border_rgb, int(210 * self._opacity))
        p.setBrush(color)
        p.setPen(border)
        p.drawRoundedRect(rect, 12, 12)
        # 小尖角
        from PyQt5.QtGui import QPolygon
        poly = QPolygon()
        tip_x = w // 2
        tip_y1 = h - 20
        tip_y2 = h - 5
        poly << QPoint(tip_x - 8, tip_y1) << QPoint(tip_x + 8, tip_y1) << QPoint(tip_x, tip_y2)
        # 尖角内部填充同气泡背景
        p.setBrush(color)
        p.drawPolygon(poly)
        # 文字
        text_color = QColor(*text_rgb, int(255 * self._opacity))
        p.setPen(text_color)
        font = QFont("Microsoft YaHei", 10)
        p.setFont(font)
        p.drawText(rect, Qt.AlignCenter | Qt.TextWordWrap, self._text)
        p.end()

    def showBubble(self, text, duration=4000):
        # ====== 先清掉所有老动画/老定时（根治：欢迎语遗留singleShot关掉4秒自动新气泡的bug）======
        self._hide_timer.stop()                       # 旧"定时隐藏"立刻作废，别影响新台词
        fade_in = getattr(self, "_fade_in", None)
        if fade_in is not None and fade_in.isActive():
            fade_in.stop()
        fade_out = getattr(self, "_fade_out", None)
        if fade_out is not None and fade_out.isActive():
            fade_out.stop()                            # 如果上一句还在淡出，立刻停下，不要把新台词也弄透明+隐藏

        self.setText(text)
        self._opacity = 0.0
        self.show()
        # 淡入动画（每次都重建一个全新干净的 fade in 实例）
        self._fade_in = QTimer(self)
        self._fade_in.timeout.connect(self._doFadeIn)
        self._fade_in_step = 0
        self._fade_in.start(20)
        # 定时消失：用我们持有的 self._hide_timer 替代全局 QTimer.singleShot → 可被下一次 showBubble stop
        if duration > 0:
            self._hide_timer.start(duration)

    def _doFadeIn(self):
        self._opacity_step = getattr(self, "_opacity_step", 0)
        self._opacity += 0.08
        if self._opacity >= 1.0:
            self._opacity = 1.0
            self._fade_in.stop()
        self.update()

    def hideBubble(self):
        self._fade_out = QTimer(self)
        self._fade_out.timeout.connect(self._doFadeOut)
        self._fade_out.start(20)

    def _doFadeOut(self):
        self._opacity -= 0.08
        if self._opacity <= 0:
            self._opacity = 0
            self._fade_out.stop()
            self.hide()
        self.update()


# ======================== 主桌宠窗口 ========================
class PetWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.reminders = load_reminders()
        self.current_pose = ALL_POSES[0] if ALL_POSES else "__fallback__"
        self.scale = self.settings.get("scale", 1.0)
        self.pixmaps = {}
        self._load_images()
        # 台词游标：随机起点 + 顺序推进 → 36句全轮完才重复，且启动第一句不是每次都固定
        self._quote_cursor = random.randint(0, max(0, len(XIAR_QUOTES) - 1)) if XIAR_QUOTES else 0

        # 窗口设置
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 宠物图片标签（子控件透明背景无边框；鼠标事件穿透到父窗口保证双击能触发）
        self.pet_label = QLabel(self)
        self.pet_label.setAlignment(Qt.AlignCenter)
        self.pet_label.setAttribute(Qt.WA_TranslucentBackground, True)
        self.pet_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)  # 关键：避免QLabel吞掉双击/拖拽事件
        self.pet_label.setStyleSheet("background: transparent; border: none;")
        self.setStyleSheet("background: transparent;")
        self._update_pet_image()

        # 拖动相关（阈值：轻微移动5像素内不判定拖拽，避免用户双击手抖导致双击事件失效）
        self._drag_pos = None
        self._is_dragging = False
        self._press_global_pos = None
        self._DRAG_THRESHOLD = 5

        # 气泡
        self.bubble = BubbleWidget()

        # 窗口大小
        self._resize_to_image()

        # 位置
        pos = self.settings.get("position", [200, 400])
        self.move(pos[0], pos[1])
        self._keep_on_screen()

        # 动画：浮动
        self.float_offset = 0
        self.float_timer = QTimer(self)
        self.float_timer.timeout.connect(self._do_float)
        self.float_timer.start(60)
        self._float_phase = 0

        # 自动切换姿态（35~70秒）
        self.auto_pose_timer = QTimer(self)
        self.auto_pose_timer.timeout.connect(self._auto_change_pose)
        self._schedule_auto_pose()

        # 久坐提醒
        self.sit_timer = QTimer(self)
        self.sit_timer.timeout.connect(self._sit_reminder)
        self._reset_sit_timer()

        # 提醒事项检查
        self.reminder_timer = QTimer(self)
        self.reminder_timer.timeout.connect(self._check_reminders)
        self.reminder_timer.start(30000)  # 30秒检查一次

        # 托盘
        self._init_tray()

    # ------------------ 图片加载 ------------------
    def _load_images(self):
        # 直接用扫描好的 POSE_PATHS（完全不关心文件名，只按顺序加载）
        for pose, path in POSE_PATHS.items():
            if os.path.exists(path):
                try:
                    pm = QPixmap(path)
                    if not pm.isNull():
                        self.pixmaps[pose] = pm
                except Exception:
                    pass
        if not self.pixmaps:
            # 兜底：创建一个完全透明的占位图（避免彩色方块）
            pm = QPixmap(200, 200)
            pm.fill(Qt.transparent)
            self.pixmaps["__fallback__"] = pm

    def _fallback_pose(self):
        """兜底取任意已加载姿态（不再依赖"idle"这类特定命名）"""
        if self.current_pose in self.pixmaps:
            return self.current_pose
        if ALL_POSES and ALL_POSES[0] in self.pixmaps:
            return ALL_POSES[0]
        if self.pixmaps:
            return next(iter(self.pixmaps.keys()))
        return "__fallback__"

    def _next_pose(self, exclude_current=True):
        """按文件名字典序推进到下一张（循环）；exclude_current=True 时如果总张数>1保证不重复"""
        total = len(ALL_POSES)
        if total <= 0:
            return "__fallback__"
        try:
            idx = ALL_POSES.index(self.current_pose)
        except ValueError:
            idx = 0
        # 顺序切下一张：(idx + 1) mod total（简单顺切，不跳跃）
        if not exclude_current or total == 1:
            return ALL_POSES[(idx + 1) % total]
        return ALL_POSES[(idx + 1) % total]

    def _update_pet_image(self):
        pm = self.pixmaps.get(self.current_pose, self.pixmaps.get(self._fallback_pose()))
        if pm is None:
            return
        w = int(pm.width() * self.scale)
        h = int(pm.height() * self.scale)
        scaled = pm.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.pet_label.setPixmap(scaled)
        self.pet_label.resize(scaled.size())
        self.resize(scaled.size())

    def _resize_to_image(self):
        pm = self.pixmaps.get(self.current_pose, self.pixmaps.get(self._fallback_pose()))
        if pm is None:
            self.resize(200, 200)
            return
        w = int(pm.width() * self.scale)
        h = int(pm.height() * self.scale)
        self.resize(w, h)
        self.pet_label.resize(w, h)

    # ------------------ 浮动动画 ------------------
    def _do_float(self):
        self._float_phase += 0.06
        offset = math.sin(self._float_phase) * 5
        self.float_offset = int(offset)
        self.pet_label.move(0, self.float_offset)

    # ------------------ 自动切换 ------------------
    def _schedule_auto_pose(self):
        # 以 35~70 秒的随机间隔切换姿态，避免频繁弹出台词打断工作。
        self.auto_pose_timer.setSingleShot(True)
        self.auto_pose_timer.start(random.randint(35, 70) * 1000)

    def _auto_change_pose(self):
        # 自动切换只更新姿态；台词由双击或菜单主动触发。
        self.change_pose(self._next_pose(), speak=False)
        self._schedule_auto_pose()

    # ------------------ 久坐提醒 ------------------
    def _reset_sit_timer(self):
        self.sit_timer.stop()
        if not self.settings.get("sit_enabled", True):
            return
        minutes = self.settings.get("sit_interval", 30)
        if minutes <= 0:
            return
        self.sit_timer.start(minutes * 60 * 1000)

    def _sit_reminder(self):
        self.show_quote(f"⏰ 已经坐了{self.settings.get('sit_interval', 30)}分钟啦，站起来活动一下吧！")

    # ------------------ 提醒事项 ------------------
    def _check_reminders(self):
        from datetime import datetime
        now = datetime.now()
        now_str = now.strftime("%H:%M")
        for r in list(self.reminders):
            if r.get("time") == now_str and not r.get("done"):
                self.show_quote(f"📋 待办提醒：{r.get('text', '')}")
                r["done"] = True
                save_reminders(self.reminders)
                QTimer.singleShot(60000, self._reset_reminder_flags)

    def _reset_reminder_flags(self):
        for r in self.reminders:
            r["done"] = False
        save_reminders(self.reminders)

    # ------------------ 托盘 ------------------
    def _init_tray(self):
        self.tray = QSystemTrayIcon(self)
        # 托盘图标：直接取当前兜底姿态（不依赖任何特定命名），没有就取第一张已加载
        pm = self.pixmaps.get(self._fallback_pose())
        if pm is None and len(self.pixmaps) > 0:
            pm = next(iter(self.pixmaps.values()))
        if pm is not None:
            self.tray.setIcon(QIcon(pm.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)))
        self.tray.setToolTip("虾仁桌宠 （单击图标显示桌宠）")
        tray_menu = QMenu()
        act_show = QAction("🙂 显示桌宠", self)
        act_show.triggered.connect(self._show_from_tray)
        act_hide = QAction("🙈 隐藏到托盘", self)
        act_hide.triggered.connect(self._hide_to_tray)
        act_quit = QAction("❌ 退出", self)
        act_quit.triggered.connect(self._quit_app)
        tray_menu.addAction(act_show)
        tray_menu.addAction(act_hide)
        tray_menu.addSeparator()
        tray_menu.addAction(act_quit)
        self.tray.setContextMenu(tray_menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _on_tray_activated(self, reason):
        # 单击 / 双击 / 中键 任意方式都显示桌宠（隐藏后找回来超简单）
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick, QSystemTrayIcon.MiddleClick):
            self._show_from_tray()

    def _show_from_tray(self):
        self.show()
        self.raise_()
        self.activateWindow()
        # 显示桌宠后顺便把它带回屏幕可见区（兼容分辨率变化）。
        self._keep_on_screen()

    def _hide_to_tray(self):
        self.hide()
        self.bubble.hideBubble()
        # 隐藏后给个托盘提示，告诉用户怎么回来
        if self.tray.isVisible():
            self.tray.showMessage("虾仁桌宠", "桌宠已隐藏到托盘，单击托盘图标即可显示回来",
                                  QSystemTrayIcon.Information, 2500)

    def _quit_app(self):
        self._save_pos()
        save_settings(self.settings)
        QApplication.quit()

    # ------------------ 位置保存 ------------------
    def _save_pos(self):
        self.settings["position"] = [self.x(), self.y()]
        save_settings(self.settings)

    # ------------------ 切换姿态 ------------------
    def change_pose(self, pose, speak=True):
        if pose not in self.pixmaps:
            pose = self._fallback_pose()
        self.current_pose = pose
        self._animate_change_pose()
        if speak:
            # 台词按 36 句循环轮询：一轮用完才开始下一轮，中间不重复。
            self.show_quote()

    def _keep_on_screen(self):
        """把窗口限制在当前主屏可见区域内，避免旧坐标或换屏后找不到桌宠。"""
        screen = QApplication.primaryScreen().availableGeometry()
        max_x = max(screen.left(), screen.right() - self.width() + 1)
        max_y = max(screen.top(), screen.bottom() - self.height() + 1)
        x = min(max(self.x(), screen.left()), max_x)
        y = min(max(self.y(), screen.top()), max_y)
        if self.x() != x or self.y() != y:
            self.move(x, y)

    def _animate_change_pose(self):
        # 简单的淡入淡出效果
        self.pet_label.setWindowOpacity(0.3)
        self._update_pet_image()
        self._resize_to_image()
        QTimer.singleShot(100, lambda: self.pet_label.setWindowOpacity(1.0))

    # ------------------ 显示台词 ------------------
    def _next_quote(self):
        """台词循环：按顺序推进，36句全用完一遍之后再从头重复（同一轮内绝不重复）"""
        n = len(XIAR_QUOTES)
        if n == 0:
            return ""
        idx = self._quote_cursor % n
        text = XIAR_QUOTES[idx]
        self._quote_cursor = (idx + 1) % n    # 游标推进，到末尾自动回到第0句
        return text

    def show_quote(self, text=None):
        if text is None:
            text = self._next_quote()
        # 先一次性设置好内容+尺寸（只在台词变更时调用一次）
        self.bubble.setText(text)
        # 再定位气泡到人物头顶
        self._relocate_bubble()
        # 按台词字数自动调整显示时间：每10个字+1秒，最少3秒，最多4秒
        # （用户原要求；如需更长上限，把下方 min(4, ...) 中的 4 改成 6/8 即可）
        seconds = 3 + len(text) // 10
        seconds = max(3, min(4, seconds))
        duration_msec = seconds * 1000
        # 最后显示（含淡入淡出）
        self.bubble.showBubble(text, duration_msec)

    def _relocate_bubble(self):
        """只做气泡位置移动，不修改尺寸/内容 → 避免拖动时反复setText导致气泡异常变大"""
        if self.bubble.width() <= 0 or self.bubble.height() <= 0:
            return  # 还没 setText 过就不操作
        pet_center_x = self.x() + self.width() // 2
        bubble_x = pet_center_x - self.bubble.width() // 2
        bubble_y = self.y() - self.bubble.height() + 10
        self.bubble.move(bubble_x, bubble_y)

    def _position_bubble(self, text):
        """旧的合并接口（已弃用，保留兼容）——优先用 setText + _relocate_bubble 分离调用"""
        self.bubble.setText(text)
        self._relocate_bubble()

    # ------------------ 缩放 ------------------
    def set_scale(self, s):
        self.scale = s
        self.settings["scale"] = s
        save_settings(self.settings)
        self._update_pet_image()
        self._resize_to_image()

    # ------------------ 事件 ------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            self._press_global_pos = event.globalPos()  # 保存按下的全局坐标，用于阈值计算
            self._is_dragging = False
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_pos is not None and self._press_global_pos is not None:
            # 先判断是否超过双击抖动阈值
            dx = int(event.globalPos().x() - self._press_global_pos.x())
            dy = int(event.globalPos().y() - self._press_global_pos.y())
            if not self._is_dragging and (abs(dx) + abs(dy)) < self._DRAG_THRESHOLD:
                # 小于阈值：不移动窗口，保持"点击"状态让双击能触发
                event.accept()
                return
            # 已超过阈值 → 进入正式拖动
            self._is_dragging = True
            new_pos = event.globalPos() - self._drag_pos
            self.move(new_pos)
            # 拖动时气泡只跟随移动 → 不重新计算尺寸，避免变大bug
            if self.bubble.isVisible():
                self._relocate_bubble()
            event.accept()

    def moveEvent(self, event):
        # 任何窗口位置变化（程序move/系统移动/恢复/缩放完成）都同步气泡位置
        super().moveEvent(event)
        try:
            if self.bubble.isVisible():
                self._relocate_bubble()
        except Exception:
            pass

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._is_dragging:
                self._keep_on_screen()
                self._save_pos()
            self._drag_pos = None
            event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            # 双击：按扫描顺序推进下一张（change_pose 内部会自动出下一句循环台词，不用再调）
            self.change_pose(self._next_pose())

    def contextMenuEvent(self, event):
        self._show_context_menu(event.globalPos())

    # ------------------ 右键菜单 ------------------
    def _show_context_menu(self, global_pos):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background: #1e1c2e; color: #e8e0d0; border: 1px solid #d4a017; padding: 4px; }
            QMenu::item { padding: 6px 24px; border-radius: 4px; }
            QMenu::item:selected { background: rgba(212,160,23,0.2); }
            QMenu::separator { height: 1px; background: rgba(212,160,23,0.2); margin: 4px 8px; }
        """)

        # 调整大小（全范围缩小：15/25/35/42/50 → 新增 42% 档卡在 35%/50% 中间）
        size_menu = menu.addMenu("🔍 调整大小")
        scales = [
            ("极小 (15%)", 0.15),
            ("小   (25%)", 0.25),
            ("中   (35%)", 0.35),
            ("偏大 (42%)", 0.42),
            ("大   (50%)", 0.50),
        ]
        for label, s in scales:
            act = QAction(label, self)
            act.triggered.connect(lambda checked, v=s: self.set_scale(v))
            size_menu.addAction(act)

        menu.addSeparator()

        # 提醒事项
        rem_menu = menu.addMenu("📋 提醒事项")
        act_add_rem = QAction("➕ 新增提醒", self)
        act_add_rem.triggered.connect(self._add_reminder)
        rem_menu.addAction(act_add_rem)
        act_list_rem = QAction("📝 查看/删除提醒", self)
        act_list_rem.triggered.connect(self._list_reminders)
        rem_menu.addAction(act_list_rem)

        menu.addSeparator()

        # 久坐提醒
        sit_menu = menu.addMenu("⏰ 久坐提醒")
        minutes_opts = [("关闭", 0, False), ("30分钟", 30, True), ("45分钟", 45, True), ("60分钟", 60, True)]
        for label, m, enabled in minutes_opts:
            act = QAction(label, self)
            act.triggered.connect(lambda checked, mm=m, en=enabled: self._set_sit(mm, en))
            sit_menu.addAction(act)

        menu.addSeparator()

        # 隐藏 / 退出
        act_hide = QAction("🙈 隐藏到托盘", self)
        act_hide.triggered.connect(self._hide_to_tray)
        menu.addAction(act_hide)
        act_quit = QAction("❌ 退出桌宠", self)
        act_quit.triggered.connect(self._quit_app)
        menu.addAction(act_quit)

        menu.exec_(global_pos)

    # ------------------ 久坐提醒设置 ------------------
    def _set_sit(self, minutes, enabled):
        self.settings["sit_interval"] = minutes
        self.settings["sit_enabled"] = enabled
        save_settings(self.settings)
        self._reset_sit_timer()
        if enabled:
            self.show_quote(f"好哒，我会每{minutes}分钟提醒你起来活动哦~")
        else:
            self.show_quote("久坐提醒已关闭啦~")

    # ------------------ 提醒事项管理 ------------------
    def _add_reminder(self):
        text, ok1 = QInputDialog.getText(self, "新增提醒", "请输入提醒内容：")
        if not ok1 or not text.strip():
            return
        time_str, ok2 = QInputDialog.getText(self, "提醒时间", "请输入提醒时间（24小时制，格式 HH:MM，例如 09:30）：")
        if not ok2 or not time_str.strip():
            return
        # 简单校验时间格式
        import re
        if not re.match(r"^\d{1,2}:\d{2}$", time_str.strip()):
            QMessageBox.warning(self, "格式错误", "时间格式不正确，请使用 HH:MM 格式（例如 09:30）")
            return
        h, m = time_str.strip().split(":")
        try:
            h, m = int(h), int(m)
            if not (0 <= h < 24 and 0 <= m < 60):
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "格式错误", "时间值不正确")
            return
        time_str = f"{h:02d}:{m:02d}"
        self.reminders.append({"text": text.strip(), "time": time_str, "done": False})
        save_reminders(self.reminders)
        self.show_quote(f"好的，我会在每天{time_str}提醒你：{text.strip()}")

    def _list_reminders(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("提醒事项")
        dlg.resize(360, 300)
        dlg.setStyleSheet("background:#1e1c2e;color:#e8e0d0;")
        lay = QVBoxLayout(dlg)
        listw = QListWidget(dlg)
        listw.setStyleSheet("QListWidget{background:#161424;border:1px solid rgba(212,160,23,0.3);padding:4px;} QListWidget::item{padding:6px;}")
        for i, r in enumerate(self.reminders):
            listw.addItem(f"[{r.get('time','')}] {r.get('text','')}")
        lay.addWidget(listw)
        btn_lay = QHBoxLayout()
        btn_del = QPushButton("删除选中", dlg)
        btn_close = QPushButton("关闭", dlg)
        for b in (btn_del, btn_close):
            b.setStyleSheet("QPushButton{background:rgba(212,160,23,0.15);border:1px solid rgba(212,160,23,0.4);padding:6px 14px;border-radius:6px;color:#e8e0d0;} QPushButton:hover{background:rgba(212,160,23,0.3);}")
        btn_del.clicked.connect(lambda: self._delete_reminder(listw, dlg))
        btn_close.clicked.connect(dlg.accept)
        btn_lay.addWidget(btn_del)
        btn_lay.addStretch()
        btn_lay.addWidget(btn_close)
        lay.addLayout(btn_lay)
        dlg.exec_()

    def _delete_reminder(self, listw, dlg):
        row = listw.currentRow()
        if row < 0 or row >= len(self.reminders):
            return
        del self.reminders[row]
        save_reminders(self.reminders)
        # 刷新
        listw.clear()
        for i, r in enumerate(self.reminders):
            listw.addItem(f"[{r.get('time','')}] {r.get('text','')}")

    # ------------------ 关闭事件 ------------------
    def closeEvent(self, event):
        self._save_pos()
        save_settings(self.settings)
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # 关闭窗口不退出（托盘用）
    pet = PetWindow()
    pet.show()
    # 启动欢迎语
    QTimer.singleShot(1000, lambda: pet.show_quote("你来啦？我等你很久了～"))
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
