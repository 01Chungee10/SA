"""
통계 분석 패키지

통계 분석 기능 모듈을 포함하고 있습니다.
"""
import tkinter as tk
from tkinter import Toplevel
import pandas as pd

from .model import StatisticsModel
from .view import StatisticsView
from .controller import StatisticsController


def load_and_display_statistics(parent, df, filename=None):
    """감정 분석 결과에 대한 통계 분석 창 표시
    
    Args:
        parent (tk.Widget): 부모 위젯
        df (pd.DataFrame): 감정 분석 결과 데이터프레임
        filename (str, optional): 데이터 파일명
        
    Returns:
        Toplevel: 통계 분석 창
    """
    # 통계 분석 창 생성
    stats_window = Toplevel(parent)
    stats_window.title("감정 분석 통계")
    stats_window.geometry("1200x800")
    stats_window.minsize(800, 600)
    
    # 화면 중앙에 표시
    stats_window.update_idletasks()
    width = stats_window.winfo_width()
    height = stats_window.winfo_height()
    x = (stats_window.winfo_screenwidth() // 2) - (width // 2)
    y = (stats_window.winfo_screenheight() // 2) - (height // 2)
    stats_window.geometry(f'{width}x{height}+{x}+{y}')
    
    # 데이터프레임 복사본 사용 (원본 데이터 보존)
    df_copy = df.copy()
    
    # 모델, 뷰, 컨트롤러 생성
    model = StatisticsModel()
    view = StatisticsView(stats_window)
    controller = StatisticsController(stats_window, df_copy, filename)
    
    return stats_window 