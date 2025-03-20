"""
감정 분석 애플리케이션 메인 클래스 모듈
"""
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox

from gui_utils import center_window, StdoutRedirector
from configure import resource_path
from emotion_analysis_gui import EmotionAnalysisGUI


class EmotionAnalysisApp(tk.Tk):
    """감정 분석 애플리케이션 메인 클래스"""
    def __init__(self):
        super().__init__()
        self.title("현대제철인의 감정을 읽는다 - 감정 분석 프로그램")
        self.model = None
        self.initUI()
        
        # 로그 창 추가
        self.create_log_window()
        
        # 로그 메시지 리디렉션
        self.redirect_stdout()
        
        # 원래 stdout 저장
        self.original_stdout = sys.stdout
        
    def initUI(self):
        """UI 초기화"""
        self.geometry("1500x1000")
        self.resizable(True, True)
        
        # 윈도우 아이콘 설정 시도 (옵션)
        try:
            icon_path = resource_path("icon.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
            else:
                # 아이콘 파일이 없어도 오류 메시지 표시하지 않음
                print("아이콘 파일을 찾을 수 없습니다. 기본 아이콘을 사용합니다.")
        except Exception as e:
            # 아이콘 설정 오류를 무시
            print(f"아이콘 설정 중 오류가 발생했지만 무시합니다: {e}")
        
        # 화면 중앙에 위치
        center_window(self, 1500, 1000)
        
        # 종료 전 확인
        def on_closing():
            if messagebox.askokcancel("종료", "프로그램을 종료하시겠습니까?"):
                # 안전하게 리디렉션 복원 후 종료
                self.restore_stdout()
                self.destroy()
        
        self.protocol("WM_DELETE_WINDOW", on_closing)
    
    def create_log_window(self):
        """로그 출력을 위한 창 생성"""
        log_frame = ttk.LabelFrame(self, text="시스템 로그")
        log_frame.pack(fill="x", expand=False, padx=10, pady=10, side="bottom")
        
        # 스크롤바가 있는 텍스트 위젯
        self.log_text = tk.Text(log_frame, height=5, width=80, state="disabled")
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def redirect_stdout(self):
        """표준 출력을 GUI 로그 창으로 리디렉션"""
        self.redirector = StdoutRedirector(self.log_text)
        sys.stdout = self.redirector
        
    def restore_stdout(self):
        """표준 출력 리디렉션 복원"""
        if hasattr(self, 'original_stdout'):
            sys.stdout = self.original_stdout
            print("표준 출력이 복원되었습니다.")
        
    def load_model_and_start(self):
        """애플리케이션 시작 - 모델 로드는 사용자가 버튼으로 직접 수행"""
        # GUI 시작
        self.app = EmotionAnalysisGUI(self)
        print("애플리케이션이 준비되었습니다. 상단의 '감정 분석 모델 로드' 버튼을 클릭하여 분석을 시작하세요.")
        
        try:
            # GUI 루프 시작
            self.mainloop()
        finally:
            # 메인 루프 종료 후 표준 출력 복원
            self.restore_stdout() 