import sys
import os
import logging
from colorama import init, Fore, Back, Style
# 确保在Linux下也能正确初始化colorama
if os.name == 'posix':
    os.environ['TERM'] = 'xterm-256color'  # 设置终端类型为支持颜色的终端
init()  # 初始化colorama，确保跨平台支持ANSI颜色

# 独立 logger：带时间戳、不向 root 传播（避免与 root 的 handler 重复输出）。
# 注意：本模块被 core.config 引用，不能 import core.log（循环依赖），因此自建 handler。
_logger = logging.getLogger("core.print")
_logger.propagate = False
if not _logger.handlers:
    _handler = logging.StreamHandler(stream=sys.stdout)
    _handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    _logger.addHandler(_handler)
_logger.setLevel(logging.INFO)

class ColorPrinter:
    """带颜色输出的打印工具类（经 logging 输出，自动带时间戳）"""
    
    def __init__(self):
        self._fore_color = ''
        self._back_color = ''
        self._style = ''
        self._text = ''
        self._level = logging.INFO
    
    def _reset(self):
        """重置颜色和样式"""
        self._fore_color = ''
        self._back_color = ''
        self._style = ''
        self._level = logging.INFO
        return self
    
    def red(self):
        """设置前景色为红色"""
        self._fore_color = Fore.RED
        return self
    
    def green(self):
        """设置前景色为绿色"""
        self._fore_color = Fore.GREEN
        return self
    
    def yellow(self):
        """设置前景色为黄色"""
        self._fore_color = Fore.YELLOW
        return self
    
    def blue(self):
        """设置前景色为蓝色"""
        self._fore_color = Fore.BLUE
        return self
    
    def magenta(self):
        """设置前景色为洋红色"""
        self._fore_color = Fore.MAGENTA
        return self
    
    def cyan(self):
        """设置前景色为青色"""
        self._fore_color = Fore.CYAN
        return self
    
    def white(self):
        """设置前景色为白色"""
        self._fore_color = Fore.WHITE
        return self
    
    def black(self):
        """设置前景色为黑色"""
        self._fore_color = Fore.BLACK
        return self
    
    def bg_red(self):
        """设置背景色为红色"""
        self._back_color = Back.RED
        return self
    
    def bg_green(self):
        """设置背景色为绿色"""
        self._back_color = Back.GREEN
        return self
    
    def bold(self):
        """设置文本为粗体"""
        self._style = Style.BRIGHT
        return self
    
    def dim(self):
        """设置文本为暗淡"""
        self._style = Style.DIM
        return self
    
    def normal(self):
        """设置文本为普通样式"""
        self._style = Style.NORMAL
        return self
    
    def print(self, text, end='\n', file=sys.stdout):
        """打印带格式的文本（经 logging 输出，自动带时间戳；end/file 参数保留兼容但不再生效）"""
        formatted = f"{self._style}{self._back_color}{self._fore_color}{text}{Style.RESET_ALL}"
        _logger.log(self._level, formatted)
        self._reset()
        return self
    
    # 快捷方法
    def print_red(self, text, **kwargs):
        """快捷打印红色文本"""
        self.red().print(text, **kwargs)
    
    def print_green(self, text, **kwargs):
        """快捷打印绿色文本"""
        self.green().print(text, **kwargs)
    
    def print_yellow(self, text, **kwargs):
        """快捷打印黄色文本"""
        self.yellow().print(text, **kwargs)
    
    def print_blue(self, text, **kwargs):
        """快捷打印蓝色文本"""
        self.blue().print(text, **kwargs)
    
    def print_magenta(self, text, **kwargs):
        """快捷打印洋红色文本"""
        self.magenta().print(text, **kwargs)
    
    def print_cyan(self, text, **kwargs):
        """快捷打印青色文本"""
        self.cyan().print(text, **kwargs)

    def print_error(self, text, **kwargs):
        """快捷打印错误信息(红色粗体)"""
        self._level = logging.ERROR
        self.red().bold().print(text, **kwargs)
    
    def print_warning(self, text, **kwargs):
        """快捷打印警告信息(黄色粗体)"""
        self._level = logging.WARNING
        self.yellow().bold().print(text, **kwargs)
    
    def print_success(self, text, **kwargs):
        """快捷打印成功信息(绿色粗体)"""
        self.green().bold().print(text, **kwargs)
    
    def print_info(self, text, **kwargs):
        """快捷打印信息(蓝色)"""
        self.blue().print(text, **kwargs)

# 创建全局实例方便使用
printer = ColorPrinter()
def print_error(text, **kwargs):
    printer.print_error(text, **kwargs)

def print_info(text, **kwargs):
    printer.print_info(text, **kwargs)
    
def print_warning(text, **kwargs):
    printer.print_warning(text, **kwargs)
def print_success(text, **kwargs):
    printer.print_success(text, **kwargs)