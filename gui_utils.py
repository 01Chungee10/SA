"""
GUI 유틸리티 함수 모듈
"""
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from configure import resource_path
import pandas as pd
import numpy as np


def create_scrollable_text(parent, height=10, width=70, state="normal"):
    """스크롤바가 있는 텍스트 위젯 생성"""
    frame = ttk.Frame(parent)
    frame.pack(fill="both", expand=True, padx=5, pady=5)
    
    scrollbar = ttk.Scrollbar(frame)
    scrollbar.pack(side="right", fill="y")
    
    text_widget = tk.Text(frame, height=height, width=width, state=state,
                       yscrollcommand=scrollbar.set)
    text_widget.pack(side="left", fill="both", expand=True)
    
    scrollbar.config(command=text_widget.yview)
    
    return text_widget


def center_window(window, width, height):
    """창을 화면 중앙에 배치"""
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x_coordinate = int((screen_width - width) / 2)
    y_coordinate = int((screen_height - height) / 2)
    window.geometry(f"{width}x{height}+{x_coordinate}+{y_coordinate}")


class StdoutRedirector:
    """표준 출력을 GUI 텍스트 위젯으로 리디렉션하는 클래스"""
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self._original_stdout = sys.stdout
        
    def write(self, message):
        try:
            # 위젯이 존재하고 유효한지 확인
            if self.text_widget and self.text_widget.winfo_exists():
                self.text_widget.config(state="normal")
                self.text_widget.insert("end", message)
                self.text_widget.see("end")
                self.text_widget.config(state="disabled")
        except tk.TclError:
            # 위젯이 소멸된 경우 예외 무시
            pass
        except Exception as e:
            # 다른 예외는 콘솔에만 출력
            print(f"GUI 출력 오류: {str(e)}")
            
        # 원래 stdout에도 출력
        self._original_stdout.write(message)
        
    def flush(self):
        try:
            # 위젯이 존재하는 경우에만 갱신
            if self.text_widget and self.text_widget.winfo_exists():
                self.text_widget.update()
        except:
            pass
        
        # 원래 stdout도 플러시
        self._original_stdout.flush()


class TableWidget(ttk.Frame):
    """DataFrame을 테이블로 표시하는 위젯"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.df = None
        self.setup_ui()
    
    def setup_ui(self):
        """테이블 UI 설정"""
        # 스크롤바
        self.vsb = ttk.Scrollbar(self, orient="vertical")
        self.hsb = ttk.Scrollbar(self, orient="horizontal")
        
        # 트리뷰 (테이블)
        self.tree = ttk.Treeview(self, 
                                 columns=(), 
                                 show='headings',
                                 yscrollcommand=self.vsb.set,
                                 xscrollcommand=self.hsb.set)
        
        # 스크롤바 연결
        self.vsb.config(command=self.tree.yview)
        self.hsb.config(command=self.tree.xview)
        
        # 그리드 배치
        self.tree.grid(column=0, row=0, sticky='nsew')
        self.vsb.grid(column=1, row=0, sticky='ns')
        self.hsb.grid(column=0, row=1, sticky='ew')
        
        # 리사이징 설정
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
    
    def _format_value(self, value):
        """표시할 값 형식 변환"""
        if isinstance(value, float):
            # NaN 값 처리
            if np.isnan(value):
                return ""
            # 소수점 값 처리 (2자리)
            return f"{value:.2f}"
        return str(value)
    
    def set_dataframe(self, df):
        """DataFrame 설정 및 테이블 업데이트"""
        self.df = df
        self._update_table()
    
    def _update_table(self):
        """테이블 내용 업데이트"""
        # 기존 내용 초기화
        for i in self.tree.get_children():
            self.tree.delete(i)
            
        # DataFrame이 없으면 종료
        if self.df is None or self.df.empty:
            return
            
        # 컬럼 설정
        columns = list(self.df.columns)
        self.tree["columns"] = columns
        
        # 컬럼 헤더 설정
        for col in columns:
            # 컬럼 ID와 텍스트 설정
            self.tree.heading(col, text=str(col))
            
            # 컬럼 너비 설정 (컬럼 이름과 값들 중 가장 긴 것의 길이에 맞춤)
            max_len = max(
                len(str(col)),
                *[len(self._format_value(v)) for v in self.df[col].values if v is not None]
            )
            # 픽셀 단위로 변환 (대략적인 값)
            width = max(max_len * 10, 80)  # 최소 너비 80픽셀
            self.tree.column(col, width=width, minwidth=50)
        
        # 행 추가
        for i, (_, row) in enumerate(self.df.iterrows()):
            # 행 데이터 포맷팅
            values = [self._format_value(row[col]) for col in columns]
            
            # 행 태그 설정 (홀/짝 행 구분)
            tag = 'odd' if i % 2 == 0 else 'even'
            
            # 트리에 행 추가
            self.tree.insert('', 'end', values=values, tags=(tag,))
            
        # 태그별 스타일 설정
        self.tree.tag_configure('odd', background='#ffffff')
        self.tree.tag_configure('even', background='#f0f0f0')
    
    def clear(self):
        """테이블 내용 삭제"""
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.df = None


def create_labeled_entry(parent, label_text, width=None, row=None, column=None, padx=5, pady=5):
    """레이블이 있는 입력 필드 생성
    
    Args:
        parent: 부모 위젯
        label_text: 레이블 텍스트
        width: 입력 필드 너비
        row, column: 그리드 위치 (지정 시 그리드 배치)
        padx, pady: 패딩
        
    Returns:
        (프레임, 레이블, 입력 필드) 튜플
    """
    frame = ttk.Frame(parent)
    
    label = ttk.Label(frame, text=label_text)
    label.pack(side="left", padx=padx)
    
    entry = ttk.Entry(frame, width=width)
    entry.pack(side="left", fill="x", expand=True, padx=padx)
    
    if row is not None and column is not None:
        frame.grid(row=row, column=column, padx=padx, pady=pady, sticky="ew")
    
    return frame, label, entry


def show_scrollable_text(title, text_content, parent=None, width=600, height=400):
    """스크롤 가능한 텍스트 창 표시
    
    Args:
        title: 창 제목
        text_content: 표시할 텍스트 내용
        parent: 부모 창 (None이면 새 창)
        width, height: 창 크기
        
    Returns:
        생성된 Toplevel 창
    """
    if parent is None:
        window = tk.Tk()
    else:
        window = tk.Toplevel(parent)
        
    window.title(title)
    window.geometry(f"{width}x{height}")
    
    # 텍스트 위젯과 스크롤바
    frame = ttk.Frame(window)
    frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    scrollbar = ttk.Scrollbar(frame)
    scrollbar.pack(side="right", fill="y")
    
    text = tk.Text(frame, wrap="word", yscrollcommand=scrollbar.set)
    text.pack(side="left", fill="both", expand=True)
    
    scrollbar.config(command=text.yview)
    
    # 텍스트 내용 설정
    text.insert("1.0", text_content)
    text.config(state="disabled")  # 읽기 전용
    
    # 닫기 버튼
    close_button = ttk.Button(window, text="닫기", command=window.destroy)
    close_button.pack(pady=10)
    
    return window 