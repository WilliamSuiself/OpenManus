import asyncio
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTextEdit, QLineEdit, 
                            QPushButton, QVBoxLayout, QHBoxLayout, QWidget, 
                            QSplitter, QLabel, QStatusBar, QTabWidget, QFrame)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QObject, QSize
from PyQt5.QtGui import QFont, QTextCursor, QIcon, QPalette, QColor

from app.agent.manus import Manus
from app.logger import logger


class AsyncWorker(QThread):
    """处理异步任务的工作线程"""
    resultReady = pyqtSignal(str)
    errorOccurred = pyqtSignal(str)
    
    def __init__(self, agent, prompt):
        super().__init__()
        self.agent = agent
        self.prompt = prompt
        
    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.agent.run(self.prompt))
            self.resultReady.emit(result)
        except Exception as e:
            self.errorOccurred.emit(str(e))


class LogHandler(QObject):
    """处理日志输出的类"""
    logReceived = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
    
    def emit(self, record):
        # 对于loguru，record已经是格式化好的字符串
        self.logReceived.emit(record)


class OpenManusUI(QMainWindow):
    """OpenManus的Qt5界面"""
    
    def __init__(self):
        super().__init__()
        self.agent = Manus()
        self.initUI()
        self.setupLogHandler()
        self.applyStyles()
        
    def initUI(self):
        # 设置窗口属性
        self.setWindowTitle('OpenManus AI助手')
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建主分割器
        splitter = QSplitter(Qt.Vertical)
        
        # 创建选项卡
        self.tabWidget = QTabWidget()
        self.tabWidget.setTabPosition(QTabWidget.North)
        self.tabWidget.setDocumentMode(True)  # 更现代的外观
        
        # 创建聊天界面
        chatWidget = QWidget()
        chatLayout = QVBoxLayout(chatWidget)
        chatLayout.setContentsMargins(15, 15, 15, 15)  # 增加边距
        chatLayout.setSpacing(10)  # 增加组件间距
        
        # 添加标题
        titleLabel = QLabel("OpenManus 智能助手")
        titleLabel.setObjectName("titleLabel")
        chatLayout.addWidget(titleLabel)
        
        # 添加分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setObjectName("separator")
        chatLayout.addWidget(line)
        
        # 聊天历史区域
        self.chatHistory = QTextEdit()
        self.chatHistory.setReadOnly(True)
        self.chatHistory.setFont(QFont('Arial', 10))
        self.chatHistory.setObjectName("chatHistory")
        self.chatHistory.setFrameShape(QFrame.NoFrame)  # 移除边框
        chatLayout.addWidget(self.chatHistory, 1)  # 设置拉伸因子
        
        # 输入区域
        inputFrame = QFrame()
        inputFrame.setObjectName("inputFrame")
        inputLayout = QHBoxLayout(inputFrame)
        inputLayout.setContentsMargins(5, 5, 5, 5)
        
        self.inputField = QLineEdit()
        self.inputField.setPlaceholderText("输入您的问题...")
        self.inputField.setObjectName("inputField")
        self.inputField.returnPressed.connect(self.processInput)
        self.inputField.setMinimumHeight(40)  # 增加高度
        
        self.sendButton = QPushButton("发送")
        self.sendButton.setObjectName("sendButton")
        self.sendButton.clicked.connect(self.processInput)
        self.sendButton.setMinimumHeight(40)  # 增加高度
        self.sendButton.setMinimumWidth(80)  # 设置最小宽度
        
        inputLayout.addWidget(self.inputField)
        inputLayout.addWidget(self.sendButton)
        chatLayout.addWidget(inputFrame)
        
        # 添加聊天选项卡
        self.tabWidget.addTab(chatWidget, "聊天")
        
        # 创建日志选项卡
        logWidget = QWidget()
        logLayout = QVBoxLayout(logWidget)
        logLayout.setContentsMargins(15, 15, 15, 15)
        
        logTitleLabel = QLabel("系统日志")
        logTitleLabel.setObjectName("titleLabel")
        logLayout.addWidget(logTitleLabel)
        
        logLine = QFrame()
        logLine.setFrameShape(QFrame.HLine)
        logLine.setFrameShadow(QFrame.Sunken)
        logLine.setObjectName("separator")
        logLayout.addWidget(logLine)
        
        self.logView = QTextEdit()
        self.logView.setReadOnly(True)
        self.logView.setFont(QFont('Consolas', 9))
        self.logView.setObjectName("logView")
        self.logView.setFrameShape(QFrame.NoFrame)
        logLayout.addWidget(self.logView)
        
        self.tabWidget.addTab(logWidget, "日志")
        
        # 创建工具选项卡
        toolsWidget = QWidget()
        toolsLayout = QVBoxLayout(toolsWidget)
        toolsLayout.setContentsMargins(15, 15, 15, 15)
        
        toolsTitleLabel = QLabel("可用工具")
        toolsTitleLabel.setObjectName("titleLabel")
        toolsLayout.addWidget(toolsTitleLabel)
        
        toolsLine = QFrame()
        toolsLine.setFrameShape(QFrame.HLine)
        toolsLine.setFrameShadow(QFrame.Sunken)
        toolsLine.setObjectName("separator")
        toolsLayout.addWidget(toolsLine)
        
        toolsList = QTextEdit()
        toolsList.setReadOnly(True)
        toolsList.setFont(QFont('Arial', 10))
        toolsList.setObjectName("toolsList")
        toolsList.setFrameShape(QFrame.NoFrame)
        toolsList.setHtml("""
        <div style="margin: 10px;">
            <h3>OpenManus 支持的工具</h3>
            <ul>
                <li><b>Python代码执行</b> - 执行Python代码</li>
                <li><b>Google搜索</b> - 在网上搜索信息</li>
                <li><b>浏览器操作</b> - 控制浏览器进行网页浏览</li>
                <li><b>文件保存</b> - 将内容保存到本地文件</li>
            </ul>
            <p>更多工具正在开发中...</p>
        </div>
        """)
        toolsLayout.addWidget(toolsList)
        
        self.tabWidget.addTab(toolsWidget, "工具")
        
        # 添加选项卡到分割器
        splitter.addWidget(self.tabWidget)
        
        # 设置状态栏
        self.statusBar = QStatusBar()
        self.statusBar.setObjectName("statusBar")
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage('就绪')
        
        # 设置中央部件
        self.setCentralWidget(splitter)
        
        # 显示欢迎信息
        self.appendToChatHistory("系统", "欢迎使用OpenManus AI助手！请输入您的问题。")
    
    def applyStyles(self):
        """应用样式表"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border: 0;
                background: #ffffff;
            }
            QTabBar::tab {
                background: #e0e0e0;
                color: #505050;
                min-width: 80px;
                padding: 8px 15px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                color: #2979ff;
                font-weight: bold;
            }
            #titleLabel {
                color: #2979ff;
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 5px;
            }
            #separator {
                color: #e0e0e0;
                margin-bottom: 10px;
            }
            #chatHistory, #logView, #toolsList {
                background-color: #ffffff;
                border-radius: 4px;
                padding: 10px;
            }
            #inputFrame {
                background-color: #ffffff;
                border-radius: 4px;
                margin-top: 10px;
            }
            #inputField {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 5px 10px;
                background-color: #ffffff;
                selection-background-color: #2979ff;
            }
            #sendButton {
                background-color: #2979ff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
                font-weight: bold;
            }
            #sendButton:hover {
                background-color: #2196f3;
            }
            #sendButton:pressed {
                background-color: #1976d2;
            }
            #statusBar {
                background-color: #f5f5f5;
                color: #505050;
            }
        """)
    
    def setupLogHandler(self):
        # 设置日志处理器
        handler = LogHandler()
        # loguru的logger没有handlers属性，直接连接信号
        handler.logReceived.connect(self.appendToLog)
        # 使用loguru的add方法添加处理器
        logger.add(lambda msg: handler.emit(msg), level=0)
    
    @pyqtSlot(str)
    def appendToLog(self, message):
        self.logView.append(message)
        # 滚动到底部
        cursor = self.logView.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.logView.setTextCursor(cursor)
    
    def appendToChatHistory(self, sender, message):
        if sender == "用户":
            self.chatHistory.append(f'<div style="margin: 10px 0; text-align: right;"><span style="background-color: #e3f2fd; padding: 8px 12px; border-radius: 15px; display: inline-block; max-width: 80%; text-align: left;"><b>您:</b> {message}</span></div>')
        elif sender == "系统":
            self.chatHistory.append(f'<div style="margin: 10px 0; text-align: center;"><span style="color: #757575; font-style: italic;">{message}</span></div>')
        else:
            self.chatHistory.append(f'<div style="margin: 10px 0;"><span style="background-color: #f5f5f5; padding: 8px 12px; border-radius: 15px; display: inline-block; max-width: 80%;"><b>AI:</b> {message}</span></div>')
        
        # 滚动到底部
        cursor = self.chatHistory.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.chatHistory.setTextCursor(cursor)
    
    def processInput(self):
        prompt = self.inputField.text().strip()
        if not prompt:
            return
        
        # 清空输入框
        self.inputField.clear()
        
        # 显示用户输入
        self.appendToChatHistory("用户", prompt)
        
        if prompt.lower() == "exit":
            self.appendToChatHistory("系统", "再见！")
            QApplication.quit()
            return
        
        # 更新状态
        self.statusBar.showMessage('处理中...')
        self.sendButton.setEnabled(False)
        
        # 启动异步工作线程
        self.worker = AsyncWorker(self.agent, prompt)
        self.worker.resultReady.connect(self.handleResult)
        self.worker.errorOccurred.connect(self.handleError)
        self.worker.finished.connect(self.workerFinished)
        self.worker.start()
    
    @pyqtSlot(str)
    def handleResult(self, result):
        self.appendToChatHistory("AI", result)
    
    @pyqtSlot(str)
    def handleError(self, error):
        self.appendToChatHistory("系统", f"错误: {error}")
    
    def workerFinished(self):
        self.statusBar.showMessage('就绪')
        self.sendButton.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 使用Fusion风格，在所有平台上看起来一致
    
    window = OpenManusUI()
    window.show()
    
    sys.exit(app.exec_())
