"""
감정 분석 결과의 통계 분석 및 그룹핑 기능을 제공하는 모듈

이 모듈은 하위 호환성을 위해 유지되며, 새로운 패키지 구조를 사용합니다.
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import traceback
import pandas as pd
import numpy as np
from datetime import datetime
from gui_utils import TableWidget
from statistics import load_and_display_statistics

def load_statistics(parent, data):
    """감정 분석 결과 데이터에 대한 통계 분석 창 표시 (하위 호환성 유지)"""
    return load_and_display_statistics(parent, data)

class StatisticsGUI:
    """감정 분석 통계 GUI 클래스"""
    def __init__(self, parent, data):
        self.parent = parent
        self.data = data  # 분석된 데이터프레임
        self.group_columns = []  # 그룹핑에 사용할 열 목록
        self.current_stats = {}  # 현재 생성된 통계 데이터프레임
        
        # 분석 결과 파일 경로
        self.analysis_file_path = getattr(data, '_metadata', {}).get('analysis_file_path', None)
        
        # UI 설정
        self.setup_ui()
        
        # 데이터 검증 및 초기화
        self.validate_and_initialize_data()
    
    def setup_ui(self):
        """사용자 인터페이스 설정"""
        # 메인 프레임
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 상단 프레임 - 파일 정보 표시
        top_frame = ttk.Frame(self.main_frame)
        top_frame.pack(fill="x", pady=(0, 10))
        
        title_label = ttk.Label(top_frame, text="감정 분석 결과 통계", font=("Arial", 16, "bold"))
        title_label.pack(side="left", pady=5, padx=5)
        
        self.file_info_label = ttk.Label(top_frame, text="분석 파일: ")
        self.file_info_label.pack(side="left", pady=5, padx=20)
        
        self.data_info_label = ttk.Label(top_frame, text="데이터 수: ")
        self.data_info_label.pack(side="left", pady=5, padx=20)
        
        # 구분선
        separator = ttk.Separator(self.main_frame, orient='horizontal')
        separator.pack(fill='x', pady=5)
        
        # 콘텐츠 영역 프레임 (2열)
        content_frame = ttk.Frame(self.main_frame)
        content_frame.pack(fill="both", expand=True)
        
        # 좌측 열: 그룹 설정 및 데이터 제어
        left_column = ttk.Frame(content_frame)
        left_column.pack(side="left", fill="both", expand=False, padx=(0, 5))
        
        # 컬럼 선택 영역
        column_frame = ttk.LabelFrame(left_column, text="그룹핑 설정")
        column_frame.pack(fill="x", expand=False, pady=(0, 5))
        
        # 사용 가능한 열 목록
        available_columns_frame = ttk.Frame(column_frame)
        available_columns_frame.pack(fill="x", pady=5, padx=5)
        
        columns_label = ttk.Label(available_columns_frame, text="사용 가능한 열:")
        columns_label.pack(side="top", anchor="w", pady=(5, 0))
        
        # 열 선택 리스트와 스크롤바
        columns_frame = ttk.Frame(available_columns_frame)
        columns_frame.pack(fill="both", expand=True)
        
        columns_scroll = ttk.Scrollbar(columns_frame)
        columns_scroll.pack(side="right", fill="y")
        
        self.columns_listbox = tk.Listbox(columns_frame, yscrollcommand=columns_scroll.set, height=10)
        self.columns_listbox.pack(side="left", fill="both", expand=True, pady=5)
        
        columns_scroll.config(command=self.columns_listbox.yview)
        
        # 그룹 열 추가/제거 버튼
        button_frame = ttk.Frame(column_frame)
        button_frame.pack(fill="x", pady=5, padx=5)
        
        self.add_column_button = ttk.Button(button_frame, text="그룹 추가 ↓", 
                                          command=self.add_group_column)
        self.add_column_button.pack(side="left", padx=5)
        
        self.remove_column_button = ttk.Button(button_frame, text="그룹 제거 ↑", 
                                             command=self.remove_group_column)
        self.remove_column_button.pack(side="right", padx=5)
        
        # 선택된 그룹 열 목록
        group_columns_frame = ttk.Frame(column_frame)
        group_columns_frame.pack(fill="x", pady=5, padx=5)
        
        group_columns_label = ttk.Label(group_columns_frame, text="선택된 그룹핑 열:")
        group_columns_label.pack(side="top", anchor="w", pady=(5, 0))
        
        # 선택된 그룹 열 리스트와 스크롤바
        group_list_frame = ttk.Frame(group_columns_frame)
        group_list_frame.pack(fill="both", expand=True)
        
        group_scroll = ttk.Scrollbar(group_list_frame)
        group_scroll.pack(side="right", fill="y")
        
        self.group_listbox = tk.Listbox(group_list_frame, yscrollcommand=group_scroll.set, height=5)
        self.group_listbox.pack(side="left", fill="both", expand=True, pady=5)
        
        group_scroll.config(command=self.group_listbox.yview)
        
        # 분석 실행 버튼
        self.analyze_button = ttk.Button(column_frame, text="통계 분석 실행", 
                                       command=self.run_group_analysis)
        self.analyze_button.pack(fill="x", pady=10, padx=10)
        
        # 통계 타입 선택
        stats_type_frame = ttk.LabelFrame(left_column, text="통계 타입 선택")
        stats_type_frame.pack(fill="x", expand=False, pady=(5, 5))
        
        # 통계 타입 체크박스
        self.emotion_stats_var = tk.BooleanVar(value=True)
        emotion_stats_check = ttk.Checkbutton(stats_type_frame, text="감정 분류별 통계", 
                                            variable=self.emotion_stats_var)
        emotion_stats_check.pack(anchor="w", padx=10, pady=5)
        
        self.polarity_stats_var = tk.BooleanVar(value=True)
        polarity_stats_check = ttk.Checkbutton(stats_type_frame, text="주요 감정별 통계", 
                                             variable=self.polarity_stats_var)
        polarity_stats_check.pack(anchor="w", padx=10, pady=5)
        
        self.intensity_stats_var = tk.BooleanVar(value=True)
        intensity_stats_check = ttk.Checkbutton(stats_type_frame, text="감정 강도 통계", 
                                              variable=self.intensity_stats_var)
        intensity_stats_check.pack(anchor="w", padx=10, pady=5)
        
        # 통계 결과 저장 버튼
        self.save_button = ttk.Button(left_column, text="통계 결과 저장", 
                                    command=self.save_statistics)
        self.save_button.pack(fill="x", pady=10, padx=10)
        self.save_button["state"] = "disabled"
        
        # 우측 열: 통계 결과 표시
        right_column = ttk.Frame(content_frame)
        right_column.pack(side="left", fill="both", expand=True, padx=5)
        
        # 요약 통계 영역
        summary_frame = ttk.LabelFrame(right_column, text="요약 통계")
        summary_frame.pack(fill="x", expand=False, pady=(0, 5))
        
        # 요약 통계 텍스트 영역
        summary_text_frame = ttk.Frame(summary_frame)
        summary_text_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        summary_scroll = ttk.Scrollbar(summary_text_frame)
        summary_scroll.pack(side="right", fill="y")
        
        self.summary_text = tk.Text(summary_text_frame, height=10, width=70, state="disabled",
                                  yscrollcommand=summary_scroll.set)
        self.summary_text.pack(side="left", fill="both", expand=True)
        
        summary_scroll.config(command=self.summary_text.yview)
        
        # 통계 테이블 영역 - 탭으로 구성
        self.tabs = ttk.Notebook(right_column)
        self.tabs.pack(fill="both", expand=True, pady=(5, 0))
        
        # 감정 분류 통계 탭
        self.emotion_tab = ttk.Frame(self.tabs)
        self.tabs.add(self.emotion_tab, text='감정 분류 통계')
        
        # 감정 분류 통계 테이블
        self.emotion_table = TableWidget(self.emotion_tab)
        self.emotion_table.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 주요 감정 통계 탭
        self.main_emotion_tab = ttk.Frame(self.tabs)
        self.tabs.add(self.main_emotion_tab, text='주요 감정 통계')
        
        # 주요 감정 통계 테이블
        self.main_emotion_table = TableWidget(self.main_emotion_tab)
        self.main_emotion_table.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 감정 강도 통계 탭
        self.intensity_tab = ttk.Frame(self.tabs)
        self.tabs.add(self.intensity_tab, text='감정 강도 통계')
        
        # 감정 강도 통계 테이블
        self.intensity_table = TableWidget(self.intensity_tab)
        self.intensity_table.pack(fill="both", expand=True, padx=5, pady=5)
    
    def validate_and_initialize_data(self):
        """데이터 검증 및 초기화"""
        # 필수 열 확인
        required_columns = ['주요_감정', '감정_강도', '감정_분류']
        missing_columns = [col for col in required_columns if col not in self.data.columns]
        
        if missing_columns:
            err_msg = f"데이터에 필수 열이 없습니다: {', '.join(missing_columns)}"
            messagebox.showerror("데이터 오류", err_msg)
            self.parent.destroy()
            return
        
        # 파일 정보 업데이트
        if self.analysis_file_path:
            self.file_info_label.config(text=f"분석 파일: {os.path.basename(self.analysis_file_path)}")
        else:
            self.file_info_label.config(text="분석 파일: 불러온 데이터프레임")
        
        self.data_info_label.config(text=f"데이터 수: {len(self.data)}개")
        
        # 컬럼 리스트 초기화 (감정 분석 관련 컬럼 제외)
        excluded_columns = ['주요_감정', '감정_강도', '감정_분류', '감정_세부내용']
        self.available_columns = [col for col in self.data.columns if col not in excluded_columns]
        
        for col in sorted(self.available_columns):
            self.columns_listbox.insert(tk.END, col)
    
    def add_group_column(self):
        """그룹핑 열 추가"""
        selected_indices = self.columns_listbox.curselection()
        
        if not selected_indices:
            messagebox.showwarning("선택 오류", "그룹핑에 추가할 열을 선택하세요.")
            return
        
        # 선택된 모든 열 추가
        for idx in reversed(selected_indices):
            column = self.columns_listbox.get(idx)
            
            # 이미 그룹 목록에 있는 열은 추가하지 않음
            if column not in self.group_columns:
                self.group_columns.append(column)
                self.group_listbox.insert(tk.END, column)
    
    def remove_group_column(self):
        """그룹핑 열 제거"""
        selected_indices = self.group_listbox.curselection()
        
        if not selected_indices:
            messagebox.showwarning("선택 오류", "그룹핑에서 제거할 열을 선택하세요.")
            return
        
        # 선택된 모든 열 제거
        for idx in reversed(selected_indices):
            column = self.group_listbox.get(idx)
            self.group_columns.remove(column)
            self.group_listbox.delete(idx)
    
    def run_group_analysis(self):
        """그룹 분석 실행"""
        # 필수 통계 타입 선택 확인
        if not any([self.emotion_stats_var.get(), 
                    self.polarity_stats_var.get(), 
                    self.intensity_stats_var.get()]):
            messagebox.showwarning("선택 오류", "최소한 하나의 통계 유형을 선택하세요.")
            return
        
        # 결과 영역 초기화
        self.summary_text.config(state="normal")
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.config(state="disabled")
        
        # 분석 시작
        try:
            # 그룹핑 없는 경우, 전체 데이터 통계
            if not self.group_columns:
                self.analyze_overall_statistics()
            
            # 그룹핑 있는 경우, 그룹별 통계
            else:
                self.analyze_grouped_statistics()
            
            # 저장 버튼 활성화
            self.save_button["state"] = "normal"
            
        except Exception as e:
            error_msg = f"통계 분석 중 오류 발생: {str(e)}"
            messagebox.showerror("분석 오류", error_msg)
            print(error_msg)
            print(traceback.format_exc())
    
    def analyze_overall_statistics(self):
        """전체 데이터에 대한 통계 분석 실행"""
        df = self.data
        total_count = len(df)
        
        # 요약 통계 텍스트
        summary_text = f"전체 데이터 통계 분석 (총 {total_count}개 항목)\n\n"
        summary_text += "="*50 + "\n\n"
        
        # 감정 분류별 통계
        if self.polarity_stats_var.get():
            summary_text += "[감정 분류별 통계]\n"
            summary_text += "-"*40 + "\n"
            
            polarity_counts = df['감정_분류'].value_counts().sort_index()
            polarity_percent = df['감정_분류'].value_counts(normalize=True).sort_index() * 100
            
            # 감정 분류 통계 데이터프레임 생성
            emotion_stats = pd.DataFrame({
                '감정_분류': polarity_counts.index,
                '데이터수': polarity_counts.values,
                '비율(%)': polarity_percent.values.round(2)
            })
            
            # 테이블에 데이터 설정
            self.emotion_table.set_dataframe(emotion_stats)
            
            # 요약 텍스트에 추가
            for idx, polarity in enumerate(polarity_counts.index):
                count = polarity_counts.iloc[idx]
                percent = polarity_percent.iloc[idx]
                summary_text += f"{polarity}: {count}개 ({percent:.2f}%)\n"
            
            summary_text += "\n"
        else:
            self.emotion_table.clear()
        
        # 주요 감정별 통계
        if self.emotion_stats_var.get():
            summary_text += "[주요 감정별 통계]\n"
            summary_text += "-"*40 + "\n"
            
            emotion_counts = df['주요_감정'].value_counts().sort_index()
            emotion_percent = df['주요_감정'].value_counts(normalize=True).sort_index() * 100
            
            # 주요 감정 통계 데이터프레임 생성
            main_emotion_stats = pd.DataFrame({
                '주요_감정': emotion_counts.index,
                '데이터수': emotion_counts.values,
                '비율(%)': emotion_percent.values.round(2)
            })
            
            # 테이블에 데이터 설정
            self.main_emotion_table.set_dataframe(main_emotion_stats)
            
            # 상위 10개만 요약 텍스트에 표시
            top_emotions = emotion_counts.head(10)
            top_percents = emotion_percent.head(10)
            
            for idx, emotion in enumerate(top_emotions.index):
                count = top_emotions.iloc[idx]
                percent = top_percents.iloc[idx]
                summary_text += f"{emotion}: {count}개 ({percent:.2f}%)\n"
            
            if len(emotion_counts) > 10:
                summary_text += f"... 외 {len(emotion_counts) - 10}개 감정\n"
            
            summary_text += "\n"
        else:
            self.main_emotion_table.clear()
        
        # 감정 강도 통계
        if self.intensity_stats_var.get():
            summary_text += "[감정 강도 통계]\n"
            summary_text += "-"*40 + "\n"
            
            # 기술 통계량
            intensity_stats = df['감정_강도'].describe()
            
            # 감정 강도 통계 데이터프레임 생성
            intensity_df = pd.DataFrame({
                '통계': ['평균', '표준편차', '최소값', '25%', '중앙값', '75%', '최대값'],
                '값': [
                    intensity_stats['mean'],
                    intensity_stats['std'],
                    intensity_stats['min'],
                    intensity_stats['25%'],
                    intensity_stats['50%'],
                    intensity_stats['75%'],
                    intensity_stats['max']
                ]
            })
            
            # 테이블에 데이터 설정
            self.intensity_table.set_dataframe(intensity_df)
            
            # 요약 텍스트에 추가
            summary_text += f"평균: {intensity_stats['mean']:.2f}\n"
            summary_text += f"표준편차: {intensity_stats['std']:.2f}\n"
            summary_text += f"최소값: {intensity_stats['min']:.2f}\n"
            summary_text += f"최대값: {intensity_stats['max']:.2f}\n"
            summary_text += f"중앙값: {intensity_stats['50%']:.2f}\n"
            
            # 구간별 빈도
            bins = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
            labels = ['0-0.2', '0.2-0.4', '0.4-0.6', '0.6-0.8', '0.8-1.0']
            intensity_binned = pd.cut(df['감정_강도'], bins=bins, labels=labels)
            
            summary_text += "\n[감정 강도 구간별 빈도]\n"
            intensity_counts = intensity_binned.value_counts().sort_index()
            intensity_percent = intensity_binned.value_counts(normalize=True).sort_index() * 100
            
            for idx, label in enumerate(intensity_counts.index):
                count = intensity_counts.iloc[idx]
                percent = intensity_percent.iloc[idx]
                summary_text += f"{label}: {count}개 ({percent:.2f}%)\n"
            
            # 구간별 빈도 테이블에 추가
            binned_stats = pd.DataFrame({
                '강도_구간': intensity_binned.cat.categories,
                '데이터수': intensity_counts.values,
                '비율(%)': intensity_percent.values.round(2)
            })
            
            # 테이블에 데이터 추가 (기존 데이터에 구간별 빈도 추가)
            if not self.tabs.index("end") >= 4:  # 이미 구간별 탭이 있는지 확인
                self.intensity_bin_tab = ttk.Frame(self.tabs)
                self.tabs.add(self.intensity_bin_tab, text='감정 강도 구간')
                
                self.intensity_bin_table = TableWidget(self.intensity_bin_tab)
                self.intensity_bin_table.pack(fill="both", expand=True, padx=5, pady=5)
            
            # 구간별 빈도 테이블 업데이트
            self.intensity_bin_table.set_dataframe(binned_stats)
        else:
            self.intensity_table.clear()
            # 구간별 탭이 있으면 제거
            if hasattr(self, 'intensity_bin_table'):
                self.intensity_bin_table.clear()
        
        # 결과 표시
        self.summary_text.config(state="normal")
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(tk.END, summary_text)
        self.summary_text.config(state="disabled")
        
        # 통계 데이터프레임 저장
        self.current_stats = {}
        
        if self.polarity_stats_var.get():
            self.current_stats['감정_분류_통계'] = emotion_stats
            
        if self.emotion_stats_var.get():
            self.current_stats['주요_감정_통계'] = main_emotion_stats
            
        if self.intensity_stats_var.get():
            self.current_stats['감정_강도_통계'] = intensity_df
            
            # 구간별 빈도 추가
            self.current_stats['감정_강도_구간_통계'] = binned_stats
        
        # 저장 버튼 활성화
        self.save_button["state"] = "normal"
    
    def analyze_grouped_statistics(self):
        """그룹별 통계 분석 실행"""
        df = self.data
        total_count = len(df)
        
        # 요약 통계 텍스트
        group_str = ", ".join(self.group_columns)
        summary_text = f"그룹별 통계 분석 (총 {total_count}개 항목)\n"
        summary_text += f"그룹핑 컬럼: {group_str}\n\n"
        summary_text += "="*50 + "\n\n"
        
        # 그룹별 통계 계산
        grouped = df.groupby(self.group_columns)
        group_counts = grouped.size().reset_index(name='데이터수')
        
        # 감정 분류별 통계
        emotion_stats = None
        if self.polarity_stats_var.get():
            # 각 그룹별로 감정 분류 빈도 및 퍼센트 계산
            polarity_counts = pd.crosstab(
                index=[df[col] for col in self.group_columns],
                columns=df['감정_분류'],
                margins=True,
                margins_name='합계'
            )
            
            # 상대 빈도(퍼센트) 계산
            polarity_percent = pd.crosstab(
                index=[df[col] for col in self.group_columns],
                columns=df['감정_분류'],
                margins=True,
                margins_name='합계',
                normalize='index'
            ) * 100
            
            # 긍정, 부정, 중립이 없는 경우 0으로 채우기
            for col in ['긍정', '부정', '중립']:
                if col not in polarity_counts.columns:
                    polarity_counts[col] = 0
                    polarity_percent[col] = 0
            
            # 컬럼 순서 정렬
            cols = [col for col in ['긍정', '부정', '중립'] if col in polarity_counts.columns]
            cols.append('합계')
            polarity_counts = polarity_counts[cols]
            polarity_percent = polarity_percent[cols]
            
            # 결과 데이터프레임 생성
            emotion_stats = group_counts.copy()
            
            for col in polarity_counts.columns:
                if col != '합계':
                    emotion_stats[f'{col}_수'] = polarity_counts[col]
                    emotion_stats[f'{col}_%'] = polarity_percent[col].round(2)
            
            # 테이블에 데이터 설정
            self.emotion_table.set_dataframe(emotion_stats)
        else:
            self.emotion_table.clear()
        
        # 주요 감정별 통계
        main_emotion_stats = None
        if self.emotion_stats_var.get():
            # 각 그룹별로 상위 3개 주요 감정
            main_emotion_stats = pd.DataFrame()
            
            for name, group in grouped:
                # 그룹별 주요 감정 빈도
                emotion_counts = group['주요_감정'].value_counts()
                top_emotions = emotion_counts.head(3)
                
                # 그룹 이름을 튜플에서 딕셔너리로 변환
                if isinstance(name, tuple):
                    group_dict = {col: val for col, val in zip(self.group_columns, name)}
                else:
                    group_dict = {self.group_columns[0]: name}
                
                # 각 상위 감정에 대한 행 추가
                for emotion, count in top_emotions.items():
                    percent = (count / len(group)) * 100
                    row_dict = group_dict.copy()
                    row_dict.update({
                        '주요_감정': emotion,
                        '빈도': count,
                        '비율': percent.round(2)
                    })
                    main_emotion_stats = pd.concat([main_emotion_stats, pd.DataFrame([row_dict])], ignore_index=True)
            
            # 테이블에 데이터 설정
            self.main_emotion_table.set_dataframe(main_emotion_stats)
        else:
            self.main_emotion_table.clear()
        
        # 감정 강도 통계
        intensity_stats = None
        if self.intensity_stats_var.get():
            # 그룹별 감정 강도 통계
            intensity_stats = grouped['감정_강도'].agg([
                ('평균', 'mean'),
                ('중앙값', 'median'),
                ('표준편차', 'std'),
                ('최소값', 'min'),
                ('최대값', 'max')
            ]).reset_index()
            
            # NaN 값 처리
            intensity_stats = intensity_stats.fillna(0)
            
            # 소수점 두 자리로 반올림
            for col in ['평균', '중앙값', '표준편차', '최소값', '최대값']:
                intensity_stats[col] = intensity_stats[col].round(2)
            
            # 테이블에 데이터 설정
            self.intensity_table.set_dataframe(intensity_stats)
        else:
            self.intensity_table.clear()
        
        # 요약 통계 텍스트 작성
        if emotion_stats is not None:
            summary_text += "[감정 분류별 그룹 통계 요약]\n"
            summary_text += "-"*40 + "\n"
            summary_text += f"총 그룹 수: {len(group_counts)}개\n"
            summary_text += f"가장 큰 그룹 크기: {group_counts['데이터수'].max()}개\n"
            summary_text += f"가장 작은 그룹 크기: {group_counts['데이터수'].min()}개\n"
            summary_text += f"평균 그룹 크기: {group_counts['데이터수'].mean():.2f}개\n\n"
        
        if main_emotion_stats is not None:
            summary_text += "[주요 감정별 그룹 통계 요약]\n"
            summary_text += "-"*40 + "\n"
            summary_text += f"분석된 고유 주요 감정 수: {main_emotion_stats['주요_감정'].nunique()}개\n"
            
            # 전체적으로 가장 빈번한 주요 감정
            top_overall = main_emotion_stats.groupby('주요_감정')['빈도'].sum().sort_values(ascending=False).head(3)
            summary_text += "\n전체 상위 3개 주요 감정:\n"
            
            for emotion, count in top_overall.items():
                summary_text += f"- {emotion}: 총 {count}개 그룹에서 상위 등장\n"
            
            summary_text += "\n"
        
        if intensity_stats is not None:
            summary_text += "[감정 강도 그룹 통계 요약]\n"
            summary_text += "-"*40 + "\n"
            summary_text += f"평균 감정 강도 최대값: {intensity_stats['평균'].max():.2f}\n"
            summary_text += f"평균 감정 강도 최소값: {intensity_stats['평균'].min():.2f}\n"
            summary_text += f"모든 그룹 평균 감정 강도: {intensity_stats['평균'].mean():.2f}\n\n"
        
        # 요약 통계 표시
        self.summary_text.config(state="normal")
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(tk.END, summary_text)
        self.summary_text.config(state="disabled")
        
        # 통계 데이터프레임 저장 (나중에 파일로 저장하기 위해)
        self.current_stats = {}
        
        if emotion_stats is not None:
            self.current_stats['감정_분류_통계'] = emotion_stats
        
        if main_emotion_stats is not None:
            self.current_stats['주요_감정_통계'] = main_emotion_stats
        
        if intensity_stats is not None:
            self.current_stats['감정_강도_통계'] = intensity_stats
        
        # 저장 버튼 활성화
        self.save_button["state"] = "normal"
    
    def save_statistics(self):
        """통계 결과를 CSV 파일로 저장"""
        if not hasattr(self, 'current_stats') or self.current_stats is None:
            messagebox.showwarning("저장 오류", "저장할 통계 데이터가 없습니다.")
            return
        
        # 원본 파일명 추출 (있는 경우)
        if self.analysis_file_path:
            base_filename = os.path.splitext(os.path.basename(self.analysis_file_path))[0]
        else:
            base_filename = "감정분석결과"
        
        # 저장 시간 스탬프
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # 출력 폴더 확인
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 파일 경로 생성
        output_path = os.path.join(output_dir, f"{base_filename}_기술통계량_{timestamp}.xlsx")
        
        try:
            # 데이터 저장 (여러 시트에 저장)
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # 각 통계 결과를 별도의 시트에 저장
                for sheet_name, df in self.current_stats.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # 메타 정보 시트 추가
                meta_df = pd.DataFrame([{
                    '분석일시': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    '원본파일': self.analysis_file_path if self.analysis_file_path else "불러온 데이터프레임",
                    '총데이터수': len(self.data),
                    '그룹핑컬럼': ", ".join(self.group_columns) if self.group_columns else "없음"
                }])
                meta_df.to_excel(writer, sheet_name='메타정보', index=False)
            
            # 성공 메시지
            messagebox.showinfo("저장 완료", f"통계 결과가 다음 위치에 저장되었습니다:\n{output_path}")
            
        except Exception as e:
            error_msg = f"통계 결과 저장 중 오류 발생: {str(e)}"
            messagebox.showerror("저장 오류", error_msg)
            print(error_msg)
            print(traceback.format_exc()) 