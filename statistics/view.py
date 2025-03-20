"""
통계 분석 결과를 표시하는 GUI 구성요소 모듈
"""
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import colorsys

class StatisticsView:
    """통계 분석 결과를 표시하는 뷰 클래스"""
    
    def __init__(self, master, title="감정 분석 통계"):
        """뷰 초기화
        
        Args:
            master: 부모 윈도우
            title (str): 윈도우 제목
        """
        self.master = master
        self.master.title(title)
        self.master.geometry("1200x700")
        
        # 전체 프레임 구성
        self.main_frame = ttk.Frame(self.master)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 좌측 컨트롤 패널 생성
        self.setup_control_panel()
        
        # 우측 결과 표시 영역 생성
        self.setup_result_panel()
        
        # 하단 버튼 영역 생성
        self.setup_button_panel()
        
        # 기본 상태 설정
        self.info_message("통계 분석을 위한 컬럼을 선택하고 그룹 분석 실행 버튼을 클릭하세요.")
        
        # 이벤트 핸들러 설정
        self.setup_event_handlers()
    
    def setup_control_panel(self):
        """좌측 컨트롤 패널 설정"""
        self.control_frame = ttk.LabelFrame(self.main_frame, text="통계 분석 설정")
        self.control_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        # 데이터 정보 프레임
        self.data_info_frame = ttk.Frame(self.control_frame)
        self.data_info_frame.pack(fill=tk.X, expand=False, padx=5, pady=5)
        
        # 파일 정보
        ttk.Label(self.data_info_frame, text="분석 파일:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.file_info_label = ttk.Label(self.data_info_frame, text="[선택된 파일 없음]")
        self.file_info_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        # 데이터 크기 정보
        ttk.Label(self.data_info_frame, text="데이터 크기:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.data_size_label = ttk.Label(self.data_info_frame, text="0행 x 0열")
        self.data_size_label.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        # 구분선
        ttk.Separator(self.control_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5, pady=5)
        
        # 그룹 분석 프레임
        self.group_analysis_frame = ttk.LabelFrame(self.control_frame, text="그룹 분석")
        self.group_analysis_frame.pack(fill=tk.X, expand=False, padx=5, pady=5)
        
        # 그룹 컬럼 선택 영역
        self.column_select_frame = ttk.Frame(self.group_analysis_frame)
        self.column_select_frame.pack(fill=tk.X, expand=False, padx=5, pady=5)
        
        ttk.Label(self.column_select_frame, text="사용 가능한 컬럼:").pack(anchor=tk.W, padx=5, pady=2)
        
        # 사용 가능한 컬럼 목록
        self.available_columns_listbox = tk.Listbox(self.column_select_frame, width=25, height=8)
        self.available_columns_listbox.pack(fill=tk.X, expand=True, padx=5, pady=2)
        
        # 그룹 컬럼 추가/제거 버튼
        self.column_buttons_frame = ttk.Frame(self.column_select_frame)
        self.column_buttons_frame.pack(fill=tk.X, expand=False, padx=5, pady=5)
        
        self.add_column_button = ttk.Button(self.column_buttons_frame, text="추가 >>")
        self.add_column_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2, pady=2)
        
        self.remove_column_button = ttk.Button(self.column_buttons_frame, text="<< 제거")
        self.remove_column_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2, pady=2)
        
        # 선택된 그룹 컬럼 목록
        ttk.Label(self.column_select_frame, text="선택된 그룹 컬럼:").pack(anchor=tk.W, padx=5, pady=2)
        
        self.selected_columns_listbox = tk.Listbox(self.column_select_frame, width=25, height=5)
        self.selected_columns_listbox.pack(fill=tk.X, expand=True, padx=5, pady=2)
        
        # 순서 변경 버튼 추가
        self.order_buttons_frame = ttk.Frame(self.column_select_frame)
        self.order_buttons_frame.pack(fill=tk.X, expand=False, padx=5, pady=2)
        
        self.move_up_button = ttk.Button(self.order_buttons_frame, text="↑ 위로")
        self.move_up_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2, pady=2)
        
        self.move_down_button = ttk.Button(self.order_buttons_frame, text="↓ 아래로")
        self.move_down_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2, pady=2)
        
        # 분석 대상 컬럼 선택 (기본값: 감정_강도)
        self.target_column_frame = ttk.Frame(self.group_analysis_frame)
        self.target_column_frame.pack(fill=tk.X, expand=False, padx=5, pady=5)
        
        ttk.Label(self.target_column_frame, text="분석 대상 컬럼:").pack(side=tk.LEFT, padx=5, pady=2)
        
        self.target_column_var = tk.StringVar(value="감정_강도")
        self.target_column_combo = ttk.Combobox(self.target_column_frame, 
                                               textvariable=self.target_column_var,
                                               state="readonly",
                                               width=15)
        self.target_column_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=2)
        
        # 구분선
        ttk.Separator(self.control_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5, pady=5)
        
        # 빈도 분석 옵션 프레임
        self.frequency_options_frame = ttk.LabelFrame(self.control_frame, text="빈도 분석 옵션")
        self.frequency_options_frame.pack(fill=tk.X, expand=False, padx=5, pady=5)
        
        # 감정 분류 체크박스
        self.emotion_freq_var = tk.BooleanVar(value=True)
        self.emotion_freq_check = ttk.Checkbutton(self.frequency_options_frame, 
                                                text="감정 분류별 빈도 분석", 
                                                variable=self.emotion_freq_var)
        self.emotion_freq_check.pack(anchor=tk.W, padx=5, pady=2)
        
        # 강도 구간 체크박스
        self.intensity_bins_var = tk.BooleanVar(value=True)
        self.intensity_bins_check = ttk.Checkbutton(self.frequency_options_frame, 
                                                  text="감정 강도 구간별 빈도 분석", 
                                                  variable=self.intensity_bins_var)
        self.intensity_bins_check.pack(anchor=tk.W, padx=5, pady=2)
        
        # 다중 교차표 체크박스
        self.multi_crosstab_var = tk.BooleanVar(value=True)
        self.multi_crosstab_check = ttk.Checkbutton(self.frequency_options_frame, 
                                                  text="다단계 빈도표 생성", 
                                                  variable=self.multi_crosstab_var)
        self.multi_crosstab_check.pack(anchor=tk.W, padx=5, pady=2)
    
    def setup_result_panel(self):
        """우측 결과 표시 영역 설정"""
        self.result_frame = ttk.LabelFrame(self.main_frame, text="분석 결과")
        self.result_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 탭 컨트롤 생성
        self.result_notebook = ttk.Notebook(self.result_frame)
        self.result_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 통계 요약 탭
        self.stats_summary_frame = ttk.Frame(self.result_notebook)
        self.result_notebook.add(self.stats_summary_frame, text="통계 요약")
        
        # 통계 요약을 표시할 트리뷰
        self.stats_summary_tree = ttk.Treeview(self.stats_summary_frame)
        self.stats_summary_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 트리뷰 스크롤바 연결
        self.stats_summary_scroll = ttk.Scrollbar(self.stats_summary_tree, 
                                                 orient="vertical", 
                                                 command=self.stats_summary_tree.yview)
        self.stats_summary_tree.configure(yscrollcommand=self.stats_summary_scroll.set)
        self.stats_summary_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 감정 분포 탭
        self.emotion_dist_frame = ttk.Frame(self.result_notebook)
        self.result_notebook.add(self.emotion_dist_frame, text="감정 분포")
        
        # 감정 분포를 위한 프레임 구성
        self.emotion_dist_top_frame = ttk.Frame(self.emotion_dist_frame)
        self.emotion_dist_top_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 감정 분류 빈도 트리뷰
        self.emotion_freq_tree = ttk.Treeview(self.emotion_dist_top_frame)
        self.emotion_freq_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 트리뷰 스크롤바 연결
        self.emotion_freq_scroll = ttk.Scrollbar(self.emotion_freq_tree, 
                                               orient="vertical", 
                                               command=self.emotion_freq_tree.yview)
        self.emotion_freq_tree.configure(yscrollcommand=self.emotion_freq_scroll.set)
        self.emotion_freq_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 히트맵 캔버스 영역
        self.heatmap_frame = ttk.Frame(self.emotion_dist_frame)
        self.heatmap_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 그룹 분석 탭
        self.group_result_frame = ttk.Frame(self.result_notebook)
        self.result_notebook.add(self.group_result_frame, text="그룹 분석")
        
        # 그룹 분석 트리뷰
        self.group_result_tree = ttk.Treeview(self.group_result_frame)
        self.group_result_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 트리뷰 스크롤바 연결
        self.group_result_scroll = ttk.Scrollbar(self.group_result_tree, 
                                               orient="vertical", 
                                               command=self.group_result_tree.yview)
        self.group_result_tree.configure(yscrollcommand=self.group_result_scroll.set)
        self.group_result_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 다단계 빈도표 탭
        self.multi_level_frame = ttk.Frame(self.result_notebook)
        self.result_notebook.add(self.multi_level_frame, text="다단계 빈도표")
        
        # 감정분류와 주요감정 선택 라디오 버튼
        self.crosstab_option_frame = ttk.Frame(self.multi_level_frame)
        self.crosstab_option_frame.pack(fill=tk.X, expand=False, padx=5, pady=5)
        
        self.crosstab_type_var = tk.StringVar(value="emotion")
        self.emotion_radio = ttk.Radiobutton(self.crosstab_option_frame, text="감정 분류", 
                                            variable=self.crosstab_type_var, value="emotion",
                                            command=self.switch_crosstab_view)
        self.emotion_radio.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.main_emotion_radio = ttk.Radiobutton(self.crosstab_option_frame, text="주요 감정", 
                                                 variable=self.crosstab_type_var, value="main",
                                                 command=self.switch_crosstab_view)
        self.main_emotion_radio.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 다단계 빈도표 프레임
        self.crosstab_frame = ttk.Frame(self.multi_level_frame)
        self.crosstab_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 다단계 빈도표 트리뷰 - 감정 분류
        self.multi_level_tree = ttk.Treeview(self.crosstab_frame)
        self.multi_level_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 트리뷰 스크롤바 연결
        self.multi_level_scroll = ttk.Scrollbar(self.multi_level_tree, 
                                              orient="vertical", 
                                              command=self.multi_level_tree.yview)
        self.multi_level_tree.configure(yscrollcommand=self.multi_level_scroll.set)
        self.multi_level_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 다단계 빈도표 트리뷰 - 주요 감정 (초기에는 숨김)
        self.main_emotion_tree = ttk.Treeview(self.crosstab_frame)
        
        # 트리뷰 스크롤바 연결
        self.main_emotion_scroll = ttk.Scrollbar(self.main_emotion_tree, 
                                               orient="vertical", 
                                               command=self.main_emotion_tree.yview)
        self.main_emotion_tree.configure(yscrollcommand=self.main_emotion_scroll.set)
        self.main_emotion_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    def setup_button_panel(self):
        """하단 버튼 영역 설정"""
        self.button_frame = ttk.Frame(self.control_frame)
        self.button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        # 실행 버튼
        self.run_button = ttk.Button(self.button_frame, text="분석 실행", command=self.run_analysis)
        self.run_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 프로그레스 바 추가
        self.progress_bar = ttk.Progressbar(self.button_frame, orient="horizontal", length=200, mode="determinate")
        self.progress_bar.pack(side=tk.RIGHT, padx=5, pady=5, fill=tk.X, expand=True)
        
        # 상태 메시지 레이블
        self.status_label = ttk.Label(self.button_frame, text="")
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
        
        # 그룹 분석 실행 버튼
        self.run_analysis_button = ttk.Button(self.button_frame, text="그룹 분석 실행")
        self.run_analysis_button.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # 결과 저장 버튼
        self.save_results_button = ttk.Button(self.button_frame, text="결과 저장")
        self.save_results_button.pack(side=tk.RIGHT, padx=5, pady=5)
    
    def update_available_columns(self, columns):
        """사용 가능한 컬럼 목록 업데이트
        
        Args:
            columns (list): 컬럼 이름 목록
        """
        self.available_columns_listbox.delete(0, tk.END)
        for column in columns:
            self.available_columns_listbox.insert(tk.END, column)
        
        # 분석 대상 컬럼 콤보박스 업데이트
        self.target_column_combo['values'] = columns
        
        # 기본 선택 설정 - 주요_감정
        if '주요_감정' in columns:
            self.target_column_var.set('주요_감정')
        elif '감정_강도' in columns:
            self.target_column_var.set('감정_강도')
        elif len(columns) > 0:
            self.target_column_var.set(columns[0])
    
    def update_file_info(self, filename, rows, cols):
        """파일 정보 업데이트
        
        Args:
            filename (str): 파일명
            rows (int): 행 수
            cols (int): 열 수
        """
        self.file_info_label.config(text=filename)
        self.data_size_label.config(text=f"{rows}행 x {cols}열")
    
    def update_stats_summary_tree(self, df):
        """통계 요약 트리뷰 업데이트
        
        Args:
            df (pd.DataFrame): 통계 요약 데이터프레임
        """
        # 기존 항목 삭제
        for item in self.stats_summary_tree.get_children():
            self.stats_summary_tree.delete(item)
        
        # 컬럼 설정
        columns = list(df.columns)
        self.stats_summary_tree['columns'] = columns
        
        # 헤더 설정
        self.stats_summary_tree.heading('#0', text='지표')
        for col in columns:
            self.stats_summary_tree.heading(col, text=str(col))
            self.stats_summary_tree.column(col, width=100, anchor='center')
        
        # 데이터 추가
        for idx, row in df.iterrows():
            values = [row[col] for col in columns]
            self.stats_summary_tree.insert('', 'end', text=idx, values=values)
    
    def update_emotion_freq_tree(self, counts_df, percents_df):
        """감정 분류 빈도 트리뷰 업데이트
        
        Args:
            counts_df (pd.DataFrame): 빈도 데이터프레임
            percents_df (pd.DataFrame): 비율 데이터프레임
        """
        # 기존 항목 삭제
        for item in self.emotion_freq_tree.get_children():
            self.emotion_freq_tree.delete(item)
        
        # 컬럼 설정
        columns = list(counts_df.columns)
        display_columns = [f"{col} (빈도)" for col in columns] + [f"{col} (%)" for col in columns]
        self.emotion_freq_tree['columns'] = display_columns
        
        # 헤더 설정
        self.emotion_freq_tree.heading('#0', text='감정 분류')
        for i, col in enumerate(display_columns):
            self.emotion_freq_tree.heading(col, text=str(col))
            self.emotion_freq_tree.column(col, width=80, anchor='center')
        
        # 데이터 추가
        for idx in counts_df.index:
            if idx != '합계':
                count_values = [counts_df.loc[idx, col] for col in columns]
                percent_values = [f"{percents_df.loc[idx, col]:.1f}%" for col in columns]
                values = count_values + percent_values
                self.emotion_freq_tree.insert('', 'end', text=idx, values=values)
    
    def update_group_result_tree(self, df):
        """그룹 분석 결과 트리뷰 업데이트
        
        Args:
            df (pd.DataFrame): 그룹 분석 결과 데이터프레임
        """
        # 기존 항목 삭제
        for item in self.group_result_tree.get_children():
            self.group_result_tree.delete(item)
        
        # 컬럼 설정
        columns = list(df.columns)
        self.group_result_tree['columns'] = columns[1:]  # 첫 번째 컬럼은 #0에 표시
        
        # 헤더 설정
        self.group_result_tree.heading('#0', text=columns[0])
        for col in columns[1:]:
            self.group_result_tree.heading(col, text=str(col))
            self.group_result_tree.column(col, width=80, anchor='center')
        
        # 데이터 추가
        for idx, row in df.iterrows():
            values = [row[col] for col in columns[1:]]
            self.group_result_tree.insert('', 'end', text=row[columns[0]], values=values)
    
    def update_multi_level_tree(self, df):
        """다단계 빈도표 트리뷰 업데이트
        
        Args:
            df (pd.DataFrame): 다단계 빈도표 데이터프레임
        """
        # 기존 항목 삭제
        for item in self.multi_level_tree.get_children():
            self.multi_level_tree.delete(item)
        
        # 컬럼 설정
        if isinstance(df.index, pd.MultiIndex):
            index_names = df.index.names
            level_count = len(index_names)
            
            # 컬럼 헤더 설정
            columns = list(df.columns)
            self.multi_level_tree['columns'] = columns
            
            self.multi_level_tree.heading('#0', text=str(index_names[0]))
            for col in columns:
                self.multi_level_tree.heading(col, text=str(col))
                self.multi_level_tree.column(col, width=80, anchor='center')
            
            # 첫 번째 레벨
            prev_items = {}
            for idx in df.index.unique(level=0):
                item_id = self.multi_level_tree.insert('', 'end', text=idx, values=[''] * len(columns))
                prev_items[idx] = item_id
            
            # 두 번째 이상의 레벨
            for level in range(1, level_count):
                new_items = {}
                for idx_tuple in df.index.unique():
                    parent_tuple = idx_tuple[:level]
                    parent_id = prev_items.get(parent_tuple if level > 1 else parent_tuple[0])
                    
                    if parent_id and idx_tuple[level] not in new_items:
                        if level == level_count - 1:  # 마지막 레벨에서는 값을 추가
                            values = [df.loc[idx_tuple, col] for col in columns]
                            item_id = self.multi_level_tree.insert(parent_id, 'end', 
                                                                text=idx_tuple[level], 
                                                                values=values)
                        else:
                            item_id = self.multi_level_tree.insert(parent_id, 'end', 
                                                                text=idx_tuple[level], 
                                                                values=[''] * len(columns))
                        new_items[idx_tuple[:level+1]] = item_id
                
                prev_items = new_items
        else:
            # 다단계가 아닌 경우 일반적인 방식으로 표시
            columns = list(df.columns)
            self.multi_level_tree['columns'] = columns[1:]
            
            self.multi_level_tree.heading('#0', text=df.index.name or '인덱스')
            for col in columns[1:]:
                self.multi_level_tree.heading(col, text=str(col))
                self.multi_level_tree.column(col, width=80, anchor='center')
            
            for idx, row in df.iterrows():
                values = [row[col] for col in columns[1:]]
                self.multi_level_tree.insert('', 'end', text=idx, values=values)
    
    def info_message(self, message):
        """정보 메시지 표시
        
        Args:
            message (str): 표시할 메시지
        """
        self.status_label.config(text=message)
    
    def show_error(self, title, message):
        """에러 메시지 표시
        
        Args:
            title (str): 에러 대화상자 제목
            message (str): 에러 메시지
        """
        messagebox.showerror(title, message, parent=self.master)
    
    def show_warning(self, title, message):
        """경고 메시지 표시
        
        Args:
            title (str): 경고 제목
            message (str): 경고 메시지
        """
        messagebox.showwarning(title, message)
    
    def show_info(self, title, message):
        """정보 메시지 대화상자 표시
        
        Args:
            title (str): 정보 대화상자 제목
            message (str): 정보 메시지
        """
        messagebox.showinfo(title, message, parent=self.master)
    
    def get_selected_available_column(self):
        """사용 가능한 컬럼 목록에서 선택된 항목들 반환"""
        selection = self.available_columns_listbox.curselection()
        return [self.available_columns_listbox.get(i) for i in selection] if selection else []
    
    def get_selected_group_column(self):
        """선택된 그룹 컬럼 반환"""
        selection = self.selected_columns_listbox.curselection()
        if selection:
            return self.selected_columns_listbox.get(selection[0])
        return None
    
    def get_selected_group_columns(self):
        """선택된 모든 그룹 컬럼 목록 반환"""
        columns = []
        for i in range(self.selected_columns_listbox.size()):
            columns.append(self.selected_columns_listbox.get(i))
        return columns
    
    def get_target_column(self):
        """분석 대상 컬럼 반환"""
        return self.target_column_var.get()
    
    def get_analysis_options(self):
        """분석 옵션 반환"""
        return {
            'emotion_freq': self.emotion_freq_var.get(),
            'intensity_bins': self.intensity_bins_var.get(),
            'multi_crosstab': self.multi_crosstab_var.get()
        }
    
    def add_group_column(self):
        """선택한 컬럼을 그룹 컬럼 목록에 추가"""
        columns = self.get_selected_available_column()
        
        if columns:
            # 각 선택된 컬럼에 대해 처리
            added_count = 0
            for column in columns:
                # 이미 선택된 컬럼 목록 가져오기
                selected_columns = self.get_selected_group_columns()
                
                if column not in selected_columns:
                    # 그룹 컬럼 리스트박스에 추가
                    self.selected_columns_listbox.insert(tk.END, column)
                    added_count += 1
            
            if added_count > 0:
                self.info_message(f"{added_count}개 컬럼이 그룹 목록에 추가되었습니다.")
            else:
                self.info_message("모든 선택된 컬럼이 이미 그룹 목록에 있습니다.")
        else:
            self.info_message("추가할 컬럼을 선택하세요.")
    
    def remove_group_column(self):
        """선택한 컬럼을 그룹 컬럼 목록에서 제거"""
        selection = self.selected_columns_listbox.curselection()
        
        if selection:
            for idx in sorted(selection, reverse=True):
                column = self.selected_columns_listbox.get(idx)
                self.selected_columns_listbox.delete(idx)
                self.info_message(f"'{column}' 컬럼이 그룹 목록에서 제거되었습니다.")
        else:
            self.info_message("제거할 그룹 컬럼을 선택하세요.")

    def setup_event_handlers(self):
        """이벤트 핸들러 설정"""
        # 버튼이 존재하는지 확인 후 이벤트 연결
        if hasattr(self, 'move_up_button') and self.move_up_button is not None:
            self.move_up_button.config(command=self.move_column_up)
        
        if hasattr(self, 'move_down_button') and self.move_down_button is not None:
            self.move_down_button.config(command=self.move_column_down)
        
        # 추가/제거 버튼 이벤트도 확인 후 연결
        if hasattr(self, 'add_column_button') and self.add_column_button is not None:
            self.add_column_button.config(command=self.add_group_column)
        
        if hasattr(self, 'remove_column_button') and self.remove_column_button is not None:
            self.remove_column_button.config(command=self.remove_group_column)
    
    def move_column_up(self):
        """선택한 그룹 컬럼을 위로 이동"""
        selection = self.selected_columns_listbox.curselection()
        if not selection or 0 in selection:
            return
        
        # 선택된 항목을 하나씩 이동
        for idx in sorted(selection):
            # 선택된 항목과 바로 위 항목의 값을 가져옴
            item = self.selected_columns_listbox.get(idx)
            prev_item = self.selected_columns_listbox.get(idx - 1)
            
            # 두 항목의 위치를 교환
            self.selected_columns_listbox.delete(idx - 1)
            self.selected_columns_listbox.insert(idx - 1, item)
            self.selected_columns_listbox.delete(idx)
            self.selected_columns_listbox.insert(idx, prev_item)
            
            # 선택 상태 유지
            self.selected_columns_listbox.selection_clear(0, tk.END)
            self.selected_columns_listbox.selection_set(idx - 1)
    
    def move_column_down(self):
        """선택한 그룹 컬럼을 아래로 이동"""
        selection = self.selected_columns_listbox.curselection()
        if not selection:
            return
        
        last_index = self.selected_columns_listbox.size() - 1
        if last_index in selection:
            return
        
        # 맨 아래에서 시작하여 위로 올라가면서 이동
        for idx in sorted(selection, reverse=True):
            # 선택된 항목과 바로 아래 항목의 값을 가져옴
            item = self.selected_columns_listbox.get(idx)
            next_item = self.selected_columns_listbox.get(idx + 1)
            
            # 두 항목의 위치를 교환
            self.selected_columns_listbox.delete(idx + 1)
            self.selected_columns_listbox.insert(idx + 1, item)
            self.selected_columns_listbox.delete(idx)
            self.selected_columns_listbox.insert(idx, next_item)
            
            # 선택 상태 유지
            self.selected_columns_listbox.selection_clear(0, tk.END)
            self.selected_columns_listbox.selection_set(idx + 1)
    
    def display_results(self, results):
        """분석 결과 표시
        
        Args:
            results (dict): 분석 결과 딕셔너리
        """
        # 결과 표시 창 초기화
        self.clear_result_trees()
        
        # 기본 통계량 결과 표시
        if 'overall_stats' in results:
            overall_stats = results['overall_stats']
            self.update_stats_summary_tree(overall_stats)
        
        # 감정 빈도 결과 표시
        if 'emotion_counts' in results and 'emotion_percents' in results:
            emotion_counts = results['emotion_counts']
            emotion_percents = results['emotion_percents']
            self.update_emotion_freq_tree(emotion_counts, emotion_percents)
        
        # 감정 히트맵 표시
        if 'heatmap_data' in results:
            heatmap_data = results['heatmap_data']
            self.display_emotion_heatmap(heatmap_data)
        
        # 감정 강도 분포 결과 표시
        if 'intensity_stats' in results:
            intensity_stats = results['intensity_stats']
            self.update_intensity_dist_tree(intensity_stats)
        
        # 그룹별 통계 결과 표시
        if 'grouped_stats' in results:
            grouped_stats = results['grouped_stats']
            self.update_group_result_tree(grouped_stats)
        
        # 다단계 빈도표 결과 표시 - 감정 분류
        if 'crosstab_emotion' in results:
            crosstab = results['crosstab_emotion']
            self.update_multi_level_tree(crosstab)
        
        # 다단계 빈도표 결과 표시 - 주요 감정
        if 'crosstab_main' in results:
            crosstab_main = results['crosstab_main']
            self.update_main_emotion_tree(crosstab_main)
        
        # 첫 번째 탭으로 이동
        if self.result_notebook.tabs():
            self.result_notebook.select(0)
    
    def update_progress(self, value):
        """프로그레스 바 업데이트
        
        Args:
            value (float): 0~100 사이의 진행률 값
        """
        self.progress_bar["value"] = value
        self.master.update_idletasks()  # UI 업데이트
        
    def clear_result_trees(self):
        """모든 결과 트리뷰 초기화"""
        # 통계 요약 트리뷰 초기화
        for item in self.stats_summary_tree.get_children():
            self.stats_summary_tree.delete(item)
            
        # 감정 빈도 트리뷰 초기화
        for item in self.emotion_freq_tree.get_children():
            self.emotion_freq_tree.delete(item)
            
        # 그룹 결과 트리뷰 초기화
        for item in self.group_result_tree.get_children():
            self.group_result_tree.delete(item)
            
        # 다단계 빈도표 트리뷰 초기화 - 감정 분류
        for item in self.multi_level_tree.get_children():
            self.multi_level_tree.delete(item)
            
        # 다단계 빈도표 트리뷰 초기화 - 주요 감정
        for item in self.main_emotion_tree.get_children():
            self.main_emotion_tree.delete(item)
            
        # 히트맵 프레임 초기화
        for widget in self.heatmap_frame.winfo_children():
            widget.destroy()
    
    def update_intensity_dist_tree(self, df):
        """감정 강도 분포 트리뷰 업데이트
        
        Args:
            df (pd.DataFrame): 강도 분포 데이터프레임
        """
        # 기존 항목 삭제
        for item in self.stats_summary_tree.get_children():
            self.stats_summary_tree.delete(item)
            
        # 컬럼 설정
        columns = list(df.columns)
        self.stats_summary_tree['columns'] = columns
        
        # 헤더 설정
        self.stats_summary_tree.heading('#0', text='강도 구간')
        for col in columns:
            self.stats_summary_tree.heading(col, text=str(col))
            self.stats_summary_tree.column(col, width=100, anchor='center')
        
        # 데이터 추가
        for idx, row in df.iterrows():
            values = [row[col] for col in columns]
            self.stats_summary_tree.insert('', 'end', text=idx, values=values)
    
    def switch_crosstab_view(self):
        """다단계 빈도표 뷰 전환"""
        crosstab_type = self.crosstab_type_var.get()
        
        if crosstab_type == "emotion":
            # 감정 분류 트리뷰 표시
            self.main_emotion_tree.pack_forget()
            self.multi_level_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        else:
            # 주요 감정 트리뷰 표시
            self.multi_level_tree.pack_forget()
            self.main_emotion_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
    def update_main_emotion_tree(self, df):
        """주요 감정 다단계 빈도표 트리뷰 업데이트
        
        Args:
            df (pd.DataFrame): 다단계 빈도표 데이터프레임
        """
        # 기존 항목 삭제
        for item in self.main_emotion_tree.get_children():
            self.main_emotion_tree.delete(item)
            
        if df.empty:
            return
            
        # 컬럼 설정
        columns = list(df.columns)
        self.main_emotion_tree['columns'] = columns
        
        # 헤더 설정
        self.main_emotion_tree.heading('#0', text='그룹')
        for col in columns:
            self.main_emotion_tree.heading(col, text=str(col))
            self.main_emotion_tree.column(col, width=80, anchor='center')
        
        # 데이터 추가 (다단계 인덱스 처리)
        if isinstance(df.index, pd.MultiIndex):
            # 다단계 인덱스 처리
            self._populate_tree_with_multiindex(df, self.main_emotion_tree)
        else:
            # 일반 인덱스 처리
            for idx, row in df.iterrows():
                values = [row[col] for col in columns]
                self.main_emotion_tree.insert('', 'end', text=idx, values=values)
                
    def _populate_tree_with_multiindex(self, df, tree_widget):
        """다단계 인덱스를 가진 데이터프레임을 트리뷰에 채우기
        
        Args:
            df (pd.DataFrame): 다단계 인덱스를 가진 데이터프레임
            tree_widget: 트리뷰 위젯
        """
        columns = list(df.columns)
        index_names = df.index.names
        level_count = len(index_names)
        
        # 부모 항목 딕셔너리 (트리 위젯 ID 저장)
        parents = {}
        
        # 최상위 레벨 처리
        for level1_value in df.index.unique(level=0):
            # 최상위 항목 추가
            item_id = tree_widget.insert('', 'end', text=level1_value, values=[''] * len(columns))
            parents[(level1_value,)] = item_id
            
            # 1레벨만 있는 경우 값 추가
            if level_count == 1:
                try:
                    row = df.loc[level1_value]
                    if not isinstance(row, pd.DataFrame):  # 시리즈인 경우
                        values = [row[col] for col in columns]
                        for i, col in enumerate(columns):
                            tree_widget.set(item_id, column=col, value=values[i])
                except:
                    pass
        
        # 2레벨 이상 처리
        if level_count >= 2:
            for idx in df.index:
                # 모든 레벨에 대해
                for level in range(1, level_count):
                    # 현재 레벨까지의 튜플
                    current_path = idx[:level+1]
                    parent_path = idx[:level]
                    
                    # 이미 추가된 항목인지 확인
                    if current_path not in parents and parent_path in parents:
                        # 부모 항목 ID 가져오기
                        parent_id = parents[parent_path]
                        
                        # 현재 레벨 항목 추가
                        current_value = idx[level]
                        
                        # 마지막 레벨이면 값 추가
                        if level == level_count - 1:
                            try:
                                row_values = [df.loc[idx][col] for col in columns]
                                item_id = tree_widget.insert(parent_id, 'end', text=current_value, values=row_values)
                            except:
                                item_id = tree_widget.insert(parent_id, 'end', text=current_value, values=[''] * len(columns))
                        else:
                            item_id = tree_widget.insert(parent_id, 'end', text=current_value, values=[''] * len(columns))
                            
                        parents[current_path] = item_id
                        
    def display_emotion_heatmap(self, heatmap_data):
        """감정 분류 히트맵 표시
        
        Args:
            heatmap_data (dict): 히트맵 데이터
        """
        # 기존 캔버스 제거
        for widget in self.heatmap_frame.winfo_children():
            widget.destroy()
            
        if 'error' in heatmap_data:
            # 오류 메시지 표시
            error_label = ttk.Label(self.heatmap_frame, text=f"히트맵 생성 오류: {heatmap_data['error']}")
            error_label.pack(pady=10)
            return
            
        # 전체 데이터 히트맵
        overall_data = heatmap_data.get('overall', {})
        
        # 극성별 비율 계산
        polarity_percentages = heatmap_data.get('polarity_percentages', {})
        
        # 색상 정의 (긍정-파란색, 중립-회색, 부정-빨간색)
        colors = {
            '긍정': '#3366CC',  # 파란색
            '중립': '#999999',  # 회색
            '부정': '#CC3333'   # 빨간색
        }
        
        # Figure 생성
        fig, ax = plt.subplots(figsize=(4, 2))
        
        # 바 차트 생성
        categories = list(polarity_percentages.keys())
        values = [polarity_percentages[cat] for cat in categories]
        
        bar_colors = [colors[cat] for cat in categories]
        
        # 바 차트 그리기
        bars = ax.bar(categories, values, color=bar_colors)
        
        # 값과 퍼센트 표시
        for i, (bar, value, pct) in enumerate(zip(bars, values, values)):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                   f'{value:.1f}%',
                   ha='center', va='bottom', fontsize=8)
        
        # 축 설정
        ax.set_title(f'감정 분포 (총 {sum(values):.0f}건)')
        ax.set_ylim(0, max(values) * 1.2 if values else 1)  # 여백 추가
        
        # 격자선 제거
        ax.grid(False)
        
        # 캔버스에 그래프 추가
        canvas = FigureCanvasTkAgg(fig, master=self.heatmap_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True) 