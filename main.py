import time 
import json 
import requests 
import random 
from datetime import datetime, timedelta 
from kivy.app import App 
from kivy.uix.boxlayout import BoxLayout 
from kivy.uix.screenmanager import ScreenManager, Screen 
from kivy.uix.label import Label 
from kivy.uix.button import Button 
from kivy.uix.textinput import TextInput 
from kivy.uix.popup import Popup 
from kivy.uix.spinner import Spinner 
from kivy.clock import Clock
import os

# 确保配置目录存在
CONFIG_DIR = 'config'
if not os.path.exists(CONFIG_DIR):
    os.makedirs(CONFIG_DIR)

# ---------------------- 核心配置 ---------------------- 
CONFIG = { 
    "verify_code": {"expire_time": 5, "code_length": 6}, 
    "platform_verify_url": { 
        "meituan": "https://open.meituan.com/api/account/send_verify_code", 
        "eleme": "https://open.ele.me/api/account/send_verify_code" 
    }, 
    "platform_bind_url": { 
        "meituan": "https://open.meituan.com/api/account/bind", 
        "eleme": "https://open.ele.me/api/account/bind" 
    }, 
    "bound_account_path": os.path.join(CONFIG_DIR, "bound_accounts.json"), 
    "local_db": os.path.join(CONFIG_DIR, "order_records.json"), 
    "config_save_path": os.path.join(CONFIG_DIR, "threshold_config.json"), 
    "sync_interval": 20, 
    "default_deliver_delay": 15, 
    "max_order_per_batch": 10, 
    "default_threshold": 6 
}

# ---------------------- 核心功能函数 ---------------------- 
def generate_verify_code():
    return ''.join([str(random.randint(0, 9)) for _ in range(CONFIG["verify_code"]["code_length"])])

def send_verify_code(platform, phone):
    print(f"向{phone}发送{platform}验证码...")
    # 模拟发送验证码，实际项目中会调用真实API
    try:
        code = generate_verify_code()
        return {"status": True, "code": code}
    except Exception as e:
        return {"status": False, "msg": str(e)}

def bind_account_by_verify(platform, phone, input_code):
    # 模拟绑定账户，实际项目中会调用真实API
    try:
        bound_info = {
            "platform": platform,
            "phone": phone,
            "merchant_id": f"{platform}_{random.randint(1000, 9999)}",
            "api_key": f"test_api_key_{random.randint(100000, 999999)}",
            "order_sync_url": f"https://api.example.com/{platform}/orders",
            "deliver_notify_url": f"https://api.example.com/{platform}/deliver",
            "bind_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_bound_account(bound_info)
        return {"status": True, "msg": f"{platform}绑定成功"}
    except Exception as e:
        return {"status": False, "msg": str(e)}

def save_bound_account(account_info):
    try:
        # 读取现有账户
        try:
            with open(CONFIG["bound_account_path"], "r", encoding="utf-8") as f:
                bound_accounts = json.load(f)
        except:
            bound_accounts = []
        # 移除同平台账户
        bound_accounts = [acc for acc in bound_accounts if acc["platform"] != account_info["platform"]]
        # 添加新账户
        bound_accounts.append(account_info)
        # 保存
        with open(CONFIG["bound_account_path"], "w", encoding="utf-8") as f:
            json.dump(bound_accounts, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存账户失败: {e}")

def load_bound_accounts():
    try:
        with open(CONFIG["bound_account_path"], "r", encoding="utf-8") as f:
            bound_accounts = json.load(f)
        return {acc["platform"]: acc for acc in bound_accounts}
    except Exception as e:
        print(f"加载账户失败: {e}")
        return {}

def load_history_config():
    try:
        with open(CONFIG["config_save_path"], "r", encoding="utf-8") as f:
            history_config = json.load(f)
            if "high_order_threshold" in history_config and isinstance(history_config["high_order_threshold"], int) and history_config["high_order_threshold"] >= 1:
                return history_config["high_order_threshold"]
        return CONFIG["default_threshold"]
    except Exception as e:
        print(f"加载配置失败: {e}")
        return CONFIG["default_threshold"]

def save_current_config(threshold):
    current_config = {"high_order_threshold": threshold, "save_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    try:
        with open(CONFIG["config_save_path"], "w", encoding="utf-8") as f:
            json.dump(current_config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存配置失败: {e}")

def set_high_order_threshold(new_threshold):
    if new_threshold >= 1:
        save_current_config(new_threshold)
        return True
    return False

def query_order_status(order_id):
    try:
        # 尝试从本地数据库读取
        try:
            with open(CONFIG["local_db"], "r", encoding="utf-8") as f:
                orders = json.load(f)
        except:
            orders = []
        
        # 模拟查询结果
        if order_id.startswith('MT'):
            return {"status": True, "msg": f"订单号：{order_id}\n平台：美团\n同步时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n状态：已接单\n出餐时间：15分钟后\n餐品：汉堡×1, 可乐×1"}
        elif order_id.startswith('EL'):
            return {"status": True, "msg": f"订单号：{order_id}\n平台：饿了么\n同步时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n状态：已接单\n出餐时间：10分钟后\n餐品：披萨×1, 奶茶×1"}
        else:
            return {"status": False, "msg": "未查询到该订单"}
    except Exception as e:
        return {"status": False, "msg": str(e)}

def sync_double_platform_orders(bound_accounts):
    all_orders = []
    # 模拟同步订单
    for platform in bound_accounts.keys():
        # 每个平台生成2个模拟订单
        for i in range(2):
            prefix = "MT" if platform == "meituan" else "EL"
            order = {
                "orderId": f"{prefix}{random.randint(100000000, 999999999)}",
                "platform": "美团" if platform == "meituan" else "饿了么",
                "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "待出餐",
                "foods": [
                    {"name": "汉堡" if platform == "meituan" else "披萨", "quantity": 1},
                    {"name": "可乐" if platform == "meituan" else "奶茶", "quantity": 1}
                ],
                "total": 25.0 if platform == "meituan" else 45.0
            }
            all_orders.append(order)
    
    # 保存到本地数据库
    try:
        with open(CONFIG["local_db"], "w", encoding="utf-8") as f:
            json.dump(all_orders, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存订单失败: {e}")
    
    return all_orders

def set_platform_deliver_time(orders, high_threshold):
    deliver_plans = []
    for order in orders:
        deliver_time = 15 if len(orders) >= high_threshold else 10
        deliver_plans.append({
            "orderId": order["orderId"],
            "platform": order["platform"],
            "deliver_time": deliver_time
        })
    return deliver_plans

def auto_deliver_double_platform(deliver_plans, bound_accounts):
    results = []
    for plan in deliver_plans:
        results.append(f"{plan['platform']}订单{plan['orderId']}设置出餐时间为{plan['deliver_time']}分钟")
    return "\n".join(results)

# ---------------------- 页面定义 ----------------------
# 1. 首页
class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()
    
    def build_ui(self):
        # 主布局
        main_layout = BoxLayout(orientation="vertical", padding=20, spacing=20)
        
        # 标题
        title = Label(text="双平台自动出餐系统", font_size=24, bold=True, size_hint_y=0.2)
        main_layout.add_widget(title)
        
        # 功能按钮布局
        buttons_layout = BoxLayout(orientation="vertical", spacing=15, size_hint_y=0.6)
        
        # 绑定平台按钮
        bind_btn = Button(
            text="绑定平台", 
            font_size=18, 
            background_color=(0.2, 0.6, 1, 1),
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=60
        )
        bind_btn.bind(on_press=self.go_to_bind)
        buttons_layout.add_widget(bind_btn)
        
        # 订单处理按钮
        sync_btn = Button(
            text="订单同步与处理", 
            font_size=18, 
            background_color=(0.2, 0.8, 0.4, 1),
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=60
        )
        sync_btn.bind(on_press=self.go_to_sync)
        buttons_layout.add_widget(sync_btn)
        
        # 订单查询按钮
        query_btn = Button(
            text="订单状态查询", 
            font_size=18, 
            background_color=(1, 0.7, 0.2, 1),
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=60
        )
        query_btn.bind(on_press=self.go_to_query)
        buttons_layout.add_widget(query_btn)
        
        # 阈值设置按钮
        threshold_btn = Button(
            text="修改高单量阈值", 
            font_size=18, 
            background_color=(1, 0.4, 0.4, 1),
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=60
        )
        threshold_btn.bind(on_press=self.go_to_threshold)
        buttons_layout.add_widget(threshold_btn)
        
        main_layout.add_widget(buttons_layout)
        
        # 版本信息
        version_label = Label(text="版本 1.0.0", font_size=14, size_hint_y=0.1)
        main_layout.add_widget(version_label)
        
        self.add_widget(main_layout)
    
    def go_to_bind(self, instance):
        self.manager.current = "bind"
    
    def go_to_sync(self, instance):
        self.manager.current = "sync"
    
    def go_to_query(self, instance):
        self.manager.current = "query"
    
    def go_to_threshold(self, instance):
        self.manager.current = "threshold"

# 2. 平台绑定页
class BindScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bound_accounts = load_bound_accounts()
        self.generated_codes = {}
        self.countdowns = {}
        self.build_ui()
    
    def build_ui(self):
        # 主布局
        main_layout = BoxLayout(orientation="vertical", padding=20, spacing=20)
        
        # 标题
        title = Label(text="绑定外卖平台账号", font_size=22, bold=True, size_hint_y=0.1)
        main_layout.add_widget(title)
        
        # 美团账号输入布局
        meituan_layout = BoxLayout(orientation="vertical", spacing=10, size_hint_y=0.3)
        meituan_label = Label(text="美团账号设置", font_size=18)
        self.meituan_username = TextInput(
            hint_text="美团用户名/手机号", 
            font_size=16, 
            multiline=False,
            size_hint_y=None,
            height=50
        )
        
        # 验证码输入布局
        meituan_code_layout = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=50)
        self.meituan_code = TextInput(
            hint_text="验证码", 
            font_size=16, 
            multiline=False,
            size_hint_x=0.6
        )
        self.get_meituan_code_btn = Button(
            text="获取验证码", 
            font_size=14,
            background_color=(0.2, 0.6, 1, 1),
            color=(1, 1, 1, 1),
            size_hint_x=0.4
        )
        self.get_meituan_code_btn.bind(on_press=self.get_meituan_verification_code)
        meituan_code_layout.add_widget(self.meituan_code)
        meituan_code_layout.add_widget(self.get_meituan_code_btn)
        
        # 如果已有绑定信息，填充输入框
        if "meituan" in self.bound_accounts:
            self.meituan_username.text = self.bound_accounts["meituan"].get("phone", "")
            meituan_label.text = f"美团账号设置 (已绑定)"
        
        meituan_layout.add_widget(meituan_label)
        meituan_layout.add_widget(self.meituan_username)
        meituan_layout.add_widget(meituan_code_layout)
        
        # 饿了么账号输入布局
        eleme_layout = BoxLayout(orientation="vertical", spacing=10, size_hint_y=0.3)
        eleme_label = Label(text="饿了么账号设置", font_size=18)
        self.eleme_username = TextInput(
            hint_text="饿了么用户名/手机号", 
            font_size=16, 
            multiline=False,
            size_hint_y=None,
            height=50
        )
        
        # 验证码输入布局
        eleme_code_layout = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=50)
        self.eleme_code = TextInput(
            hint_text="验证码", 
            font_size=16, 
            multiline=False,
            size_hint_x=0.6
        )
        self.get_eleme_code_btn = Button(
            text="获取验证码", 
            font_size=14,
            background_color=(0.2, 0.6, 1, 1),
            color=(1, 1, 1, 1),
            size_hint_x=0.4
        )
        self.get_eleme_code_btn.bind(on_press=self.get_eleme_verification_code)
        eleme_code_layout.add_widget(self.eleme_code)
        eleme_code_layout.add_widget(self.get_eleme_code_btn)
        
        # 如果已有绑定信息，填充输入框
        if "eleme" in self.bound_accounts:
            self.eleme_username.text = self.bound_accounts["eleme"].get("phone", "")
            eleme_label.text = f"饿了么账号设置 (已绑定)"
        
        eleme_layout.add_widget(eleme_label)
        eleme_layout.add_widget(self.eleme_username)
        eleme_layout.add_widget(eleme_code_layout)
        
        # 操作按钮布局
        actions_layout = BoxLayout(orientation="vertical", spacing=10, size_hint_y=0.2)
        
        # 保存按钮
        self.save_btn = Button(
            text="保存绑定", 
            font_size=18, 
            background_color=(0.2, 0.8, 0.4, 1),
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=60
        )
        self.save_btn.bind(on_press=self.save_accounts)
        actions_layout.add_widget(self.save_btn)
        
        # 返回按钮
        back_btn = Button(
            text="返回首页", 
            font_size=16,
            background_color=(0.7, 0.7, 0.7, 1),
            color=(0, 0, 0, 1),
            size_hint_y=None,
            height=50
        )
        back_btn.bind(on_press=self.go_to_back)
        actions_layout.add_widget(back_btn)
        
        main_layout.add_widget(meituan_layout)
        main_layout.add_widget(eleme_layout)
        main_layout.add_widget(actions_layout)
        
        self.add_widget(main_layout)
    
    def get_meituan_verification_code(self, instance):
        self._send_verification_code("meituan", self.meituan_username.text, self.get_meituan_code_btn)
    
    def get_eleme_verification_code(self, instance):
        self._send_verification_code("eleme", self.eleme_username.text, self.get_eleme_code_btn)
    
    def _send_verification_code(self, platform, phone, button):
        if not phone.strip():
            self.show_popup("提示", "请先输入手机号")
            return
        
        # 模拟发送验证码
        result = send_verify_code(platform, phone)
        if result["status"]:
            # 存储验证码
            self.generated_codes[platform] = result["code"]
            # 显示验证码（仅用于测试）
            self.show_popup("验证码已发送", f"【测试模式】验证码为: {result['code']}\n请在5分钟内输入")
            # 开始倒计时
            self._start_countdown(button)
        else:
            self.show_popup("发送失败", result.get("msg", "验证码发送失败"))
    
    def _start_countdown(self, button):
        if button in self.countdowns:
            Clock.unschedule(self.countdowns[button])
        
        button.disabled = True
        button.text = f"60秒后重试"
        countdown = 60
        
        def update_countdown(dt):
            nonlocal countdown
            countdown -= 1
            if countdown > 0:
                button.text = f"{countdown}秒后重试"
            else:
                button.disabled = False
                button.text = "获取验证码"
                Clock.unschedule(update_countdown)
                if button in self.countdowns:
                    del self.countdowns[button]
        
        self.countdowns[button] = Clock.schedule_interval(update_countdown, 1)
    
    def save_accounts(self, instance):
        # 收集账号信息
        updated = False
        
        # 保存美团账号
        if self.meituan_username.text and self.meituan_code.text:
            if "meituan" in self.generated_codes and self.meituan_code.text == self.generated_codes["meituan"]:
                result = bind_account_by_verify("meituan", self.meituan_username.text, self.meituan_code.text)
                if result["status"]:
                    updated = True
                else:
                    self.show_popup("绑定失败", result.get("msg", "美团账号绑定失败"))
                    return
            else:
                self.show_popup("验证码错误", "美团验证码错误，请重新获取并输入")
                return
        
        # 保存饿了么账号
        if self.eleme_username.text and self.eleme_code.text:
            if "eleme" in self.generated_codes and self.eleme_code.text == self.generated_codes["eleme"]:
                result = bind_account_by_verify("eleme", self.eleme_username.text, self.eleme_code.text)
                if result["status"]:
                    updated = True
                else:
                    self.show_popup("绑定失败", result.get("msg", "饿了么账号绑定失败"))
                    return
            else:
                self.show_popup("验证码错误", "饿了么验证码错误，请重新获取并输入")
                return
        
        if updated:
            self.bound_accounts = load_bound_accounts()
            self.show_popup("保存成功", "账号绑定信息已保存")
            # 清空验证码
            self.meituan_code.text = ""
            self.eleme_code.text = ""
            # 刷新界面
            self.clear_widgets()
            self.build_ui()
        else:
            self.show_popup("提示", "请输入用户名和验证码进行绑定")
    
    def show_popup(self, title, content):
        popup = Popup(
            title=title,
            content=Label(text=content, font_size=16),
            size_hint=(0.8, 0.4),
            auto_dismiss=True
        )
        popup.open()
    
    def go_to_back(self, instance):
        self.manager.current = "home"

# 3. 订单处理页
class SyncScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_syncing = False
        self.build_ui()
    
    def build_ui(self):
        # 主布局
        main_layout = BoxLayout(orientation="vertical", padding=20, spacing=20)
        
        # 标题
        title = Label(text="订单同步与处理", font_size=22, bold=True, size_hint_y=0.1)
        main_layout.add_widget(title)
        
        # 订单同步按钮
        self.sync_btn = Button(
            text="开始同步订单", 
            font_size=18, 
            background_color=(0.2, 0.8, 0.4, 1),
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=60
        )
        self.sync_btn.bind(on_press=self.sync_orders)
        main_layout.add_widget(self.sync_btn)
        
        # 出餐结果显示
        self.result_label = Label(
            text="出餐结果将显示在这里", 
            font_size=16, 
            halign="left",
            valign="top",
            size_hint_y=0.5,
            text_size=(self.width * 0.9, None)
        )
        main_layout.add_widget(self.result_label)
        
        # 返回按钮
        back_btn = Button(
            text="返回首页", 
            font_size=16,
            background_color=(0.7, 0.7, 0.7, 1),
            color=(0, 0, 0, 1),
            size_hint_y=None,
            height=50
        )
        back_btn.bind(on_press=self.go_back)
        main_layout.add_widget(back_btn)
        
        self.add_widget(main_layout)
    
    def sync_orders(self, instance):
        if self.is_syncing:
            return
        
        self.is_syncing = True
        self.sync_btn.text = "同步中..."
        self.sync_btn.disabled = True
        self.result_label.text = "正在加载绑定的平台..."
        
        # 使用Clock延迟执行，避免界面卡顿
        Clock.schedule_once(self._do_sync_orders, 0.1)
    
    def _do_sync_orders(self, dt):
        try:
            # 加载绑定的账户
            bound_accounts = load_bound_accounts()
            if not bound_accounts:
                self.result_label.text = "未绑定任何平台，请先去「绑定平台」页操作"
                return
            
            # 同步订单
            self.result_label.text = "正在同步美团/饿了么订单..."
            orders = sync_double_platform_orders(bound_accounts)
            if not orders:
                self.result_label.text = "未同步到待出餐订单"
                return
            
            # 设置出餐时间并执行
            high_threshold = load_history_config()
            self.result_label.text = f"同步到{len(orders)}个订单，正在按阈值处理..."
            
            # 延迟一下，模拟处理时间
            Clock.schedule_once(lambda dt: self._process_orders(orders, high_threshold, bound_accounts), 0.5)
        except Exception as e:
            self.result_label.text = f"同步过程中出错: {str(e)}"
            self._reset_sync_button()
    
    def _process_orders(self, orders, high_threshold, bound_accounts):
        try:
            deliver_plans = set_platform_deliver_time(orders, high_threshold)
            result = auto_deliver_double_platform(deliver_plans, bound_accounts)
            self.result_label.text = f"处理完成！\n{result}"
        except Exception as e:
            self.result_label.text = f"处理过程中出错: {str(e)}"
        finally:
            self._reset_sync_button()
    
    def _reset_sync_button(self):
        self.is_syncing = False
        self.sync_btn.text = "开始同步订单"
        self.sync_btn.disabled = False
    
    def go_back(self, instance):
        self.manager.current = "home"

# 4. 订单查询页
class QueryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()
    
    def build_ui(self):
        # 主布局
        main_layout = BoxLayout(orientation="vertical", padding=20, spacing=20)
        
        # 标题
        title = Label(text="订单状态查询", font_size=22, bold=True, size_hint_y=0.1)
        main_layout.add_widget(title)
        
        # 订单号输入框
        self.order_input = TextInput(
            hint_text="请输入要查询的订单号",
            font_size=18,
            multiline=False,
            size_hint_y=None,
            height=50
        )
        main_layout.add_widget(self.order_input)
        
        # 查询按钮
        query_btn = Button(
            text="开始查询", 
            font_size=18, 
            background_color=(1, 0.7, 0.2, 1),
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=60
        )
        query_btn.bind(on_press=self.do_query)
        main_layout.add_widget(query_btn)
        
        # 查询结果显示
        self.result_label = Label(
            text="查询结果将显示在这里", 
            font_size=16, 
            halign="left",
            valign="top",
            size_hint_y=0.5,
            text_size=(self.width * 0.9, None)
        )
        main_layout.add_widget(self.result_label)
        
        # 返回按钮
        back_btn = Button(
            text="返回首页", 
            font_size=16,
            background_color=(0.7, 0.7, 0.7, 1),
            color=(0, 0, 0, 1),
            size_hint_y=None,
            height=50
        )
        back_btn.bind(on_press=self.go_back)
        main_layout.add_widget(back_btn)
        
        self.add_widget(main_layout)
    
    def do_query(self, instance):
        order_id = self.order_input.text.strip()
        if not order_id:
            self.show_popup("提示", "请输入订单号")
            return
        
        # 查询订单状态
        self.result_label.text = f"正在查询订单 {order_id}..."
        
        # 使用Clock延迟执行，避免界面卡顿
        Clock.schedule_once(lambda dt: self._process_query(order_id), 0.1)
    
    def _process_query(self, order_id):
        res = query_order_status(order_id)
        if res["status"]:
            self.result_label.text = res["msg"]
        else:
            self.result_label.text = res["msg"]
            self.show_popup("查询失败", res["msg"])
    
    def show_popup(self, title, content):
        popup = Popup(
            title=title,
            content=Label(text=content, font_size=16),
            size_hint=(0.8, 0.4),
            auto_dismiss=True
        )
        popup.open()
    
    def go_back(self, instance):
        self.manager.current = "home"

# 5. 阈值修改页
class ThresholdScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_threshold = load_history_config()
        self.build_ui()
    
    def build_ui(self):
        # 主布局
        main_layout = BoxLayout(orientation="vertical", padding=20, spacing=20)
        
        # 标题
        title = Label(text="修改高单量阈值", font_size=22, bold=True, size_hint_y=0.1)
        main_layout.add_widget(title)
        
        # 当前阈值显示
        current_label = Label(
            text=f"当前高单量阈值：≥{self.current_threshold}单", 
            font_size=18,
            size_hint_y=0.1
        )
        main_layout.add_widget(current_label)
        
        # 新阈值输入框
        self.threshold_input = TextInput(
            hint_text="请输入新的阈值（如6、8）",
            font_size=18,
            input_filter="int",
            multiline=False,
            size_hint_y=None,
            height=50
        )
        main_layout.add_widget(self.threshold_input)
        
        # 确认修改按钮
        save_btn = Button(
            text="确认修改", 
            font_size=18, 
            background_color=(0.2, 0.6, 1, 1),
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=60
        )
        save_btn.bind(on_press=self.save_threshold)
        main_layout.add_widget(save_btn)
        
        # 结果显示
        self.result_label = Label(
            text="", 
            font_size=16,
            size_hint_y=0.2
        )
        main_layout.add_widget(self.result_label)
        
        # 返回按钮
        back_btn = Button(
            text="返回首页", 
            font_size=16,
            background_color=(0.7, 0.7, 0.7, 1),
            color=(0, 0, 0, 1),
            size_hint_y=None,
            height=50
        )
        back_btn.bind(on_press=self.go_back)
        main_layout.add_widget(back_btn)
        
        self.add_widget(main_layout)
    
    def save_threshold(self, instance):
        new_threshold = self.threshold_input.text.strip()
        if not new_threshold.isdigit():
            self.result_label.text = "请输入有效的数字"
            return
        
        new_threshold = int(new_threshold)
        if new_threshold < 1:
            self.result_label.text = "阈值必须大于0"
            return
        
        if set_high_order_threshold(new_threshold):
            self.current_threshold = new_threshold
            self.result_label.text = f"阈值修改成功！新的阈值为：≥{new_threshold}单"
            self.show_popup("修改成功", f"高单量阈值已修改为：≥{new_threshold}单")
        else:
            self.result_label.text = "阈值修改失败，请重试"
    
    def show_popup(self, title, content):
        popup = Popup(
            title=title,
            content=Label(text=content, font_size=16),
            size_hint=(0.8, 0.4),
            auto_dismiss=True
        )
        popup.open()
    
    def go_back(self, instance):
        self.manager.current = "home"

# 主应用类
class FoodDeliveryApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(BindScreen(name='bind'))
        sm.add_widget(SyncScreen(name='sync'))
        sm.add_widget(QueryScreen(name='query'))
        sm.add_widget(ThresholdScreen(name='threshold'))
        return sm

# 程序入口
if __name__ == '__main__':
    FoodDeliveryApp().run()