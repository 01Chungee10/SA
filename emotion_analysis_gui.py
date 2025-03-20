"""
감정 분석 GUI 컴포넌트 모듈
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import traceback
import pandas as pd
from datetime import datetime

from KOTE_load import load_custom_model
from text_SentimentAnalysis import analyze_text
from file_SentimentAnalysis import load_file, analyze_file
from statistics import load_and_display_statistics
from configure import setup_device, log_work, LABELS


class EmotionAnalysisGUI:
    """감정 분석 GUI 클래스"""
    def __init__(self, parent, model=None):
        self.parent = parent
        self.model = model
        self.loaded_data = None  # 불러온 데이터 저장 변수
        self.analyzed_data = None  # 감정 분석된 데이터프레임
        self.columns = []  # 데이터 컬럼 목록
        self.file_path = None  # 선택한 파일 경로
        self.analyze_enabled = model is not None  # 모델이 로드되었는지 여부
        
        # UI 설정
        self.setup_ui()
        
        # 모델이 로드되지 않았으면 컨트롤 비활성화
        self.toggle_analyze_controls(self.analyze_enabled)
        
    def setup_ui(self):
        """사용자 인터페이스 설정"""
        # 메인 프레임
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 좌측 컬럼 (60% 너비로 조정)
        left_column = ttk.Frame(main_frame)
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 우측 컬럼 (40% 너비로 조정)
        right_column = ttk.Frame(main_frame)
        right_column.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        # 좌측 상단: 직접 입력 프레임 (텍스트 입력)
        direct_input_frame = ttk.LabelFrame(left_column, text="텍스트 직접 입력")
        direct_input_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 텍스트 입력 영역
        self.input_text = tk.Text(direct_input_frame, height=10, width=40)
        self.input_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 스크롤바
        input_scroll = ttk.Scrollbar(direct_input_frame, orient="vertical", command=self.input_text.yview)
        input_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.input_text.configure(yscrollcommand=input_scroll.set)
        
        # 직접 입력 분석 버튼
        direct_button_frame = ttk.Frame(left_column)
        direct_button_frame.pack(fill=tk.X, pady=5)
        
        self.direct_analyze_button = ttk.Button(direct_button_frame, text="텍스트 감정 분석", 
                                             command=self.analyze_direct_input)
        self.direct_analyze_button.pack(side=tk.RIGHT, padx=5)
        
        # 좌측 중앙: 파일 분석 프레임
        file_frame = ttk.LabelFrame(left_column, text="파일 감정 분석")
        file_frame.pack(fill=tk.X, expand=False, padx=5, pady=5)
        
        # 파일 선택 버튼
        self.file_button = ttk.Button(file_frame, text="파일 선택", command=self.select_file)
        self.file_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 컬럼 선택 콤보박스
        ttk.Label(file_frame, text="분석 컬럼:").pack(side=tk.LEFT, padx=5, pady=5)
        self.column_combo = ttk.Combobox(file_frame, width=15, state="disabled")
        self.column_combo.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 파일 분석 버튼
        self.file_analyze_button = ttk.Button(file_frame, text="파일 감정 분석", 
                                           command=self.analyze_file, state="disabled")
        self.file_analyze_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 좌측 하단: 결과 표시 영역
        result_frame = ttk.LabelFrame(left_column, text="분석 결과")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 결과 텍스트 영역
        result_text_frame = ttk.Frame(result_frame)
        result_text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 결과 텍스트 스크롤바
        result_scroll = ttk.Scrollbar(result_text_frame, orient="vertical")
        result_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.result_text = tk.Text(result_text_frame, height=15, width=40, state="disabled", 
                                yscrollcommand=result_scroll.set)
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        result_scroll.config(command=self.result_text.yview)
        
        # 우측 상단: 모델 및 설정 프레임
        model_frame = ttk.LabelFrame(right_column, text="모델 설정")
        model_frame.pack(fill=tk.X, pady=5)
        
        # 모델 로드 버튼
        self.load_model_button = ttk.Button(model_frame, text="모델 불러오기", command=self.load_emotion_model)
        self.load_model_button.pack(fill=tk.X, padx=5, pady=5)
        
        # 모델 상태 표시
        self.model_status_label = ttk.Label(model_frame, text="모델 상태: 로드되지 않음", foreground="red")
        self.model_status_label.pack(fill=tk.X, padx=5, pady=5)
        
        # 우측 중앙: 파일 정보 프레임
        file_info_frame = ttk.LabelFrame(right_column, text="파일 정보")
        file_info_frame.pack(fill=tk.X, pady=5)
        
        # 파일 라벨
        self.file_label = ttk.Label(file_info_frame, text="선택된 파일:")
        self.file_label.pack(fill=tk.X, padx=5, pady=(5, 0))
        
        self.stats_file_label = ttk.Label(file_info_frame, text="분석 결과 파일: 없음")
        self.stats_file_label.pack(fill=tk.X, padx=5, pady=(5, 0))
        
        # 파일 정보 스크롤바
        file_info_scroll = ttk.Scrollbar(file_info_frame, orient="vertical")
        file_info_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 파일 정보 텍스트 영역
        self.file_info_text = tk.Text(file_info_frame, height=5, width=30, state="disabled",
                                    yscrollcommand=file_info_scroll.set)
        self.file_info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        file_info_scroll.config(command=self.file_info_text.yview)
        
        # 결과 파일 불러오기 버튼
        self.load_stats_button = ttk.Button(file_info_frame, text="분석 결과 파일 불러오기", 
                                         command=self.load_analysis_result_file)
        self.load_stats_button.pack(fill=tk.X, padx=5, pady=5)
        
        # 우측 하단: 통계 요약 프레임
        stats_frame = ttk.LabelFrame(right_column, text="통계 정보")
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 통계 분석 버튼 - 통계 요약 프레임 상단으로 이동
        self.open_stats_button = ttk.Button(stats_frame, text="통계 분석 창 열기", 
                                         command=self.open_statistics_window, state="disabled")
        self.open_stats_button.pack(fill=tk.X, padx=5, pady=5)
        
        # 통계 요약 스크롤바 및 텍스트 영역
        stats_summary_frame = ttk.Frame(stats_frame)
        stats_summary_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        stats_summary_scroll = ttk.Scrollbar(stats_summary_frame, orient="vertical")
        stats_summary_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.stats_summary_area = tk.Text(stats_summary_frame, height=15, width=30, state="disabled",
                                       yscrollcommand=stats_summary_scroll.set)
        self.stats_summary_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        stats_summary_scroll.config(command=self.stats_summary_area.yview)
    
    def toggle_analyze_controls(self, enabled=True):
        """분석 관련 컨트롤 활성화/비활성화"""
        state = "normal" if enabled else "disabled"
        self.direct_analyze_button["state"] = state
        self.file_button["state"] = state
        self.load_stats_button["state"] = state
        
        # 상태에 따라 모델 상태 라벨 업데이트
        if enabled:
            self.model_status_label.config(text="모델 상태: 로드됨", foreground="green")
        else:
            self.model_status_label.config(text="모델 상태: 로드되지 않음", foreground="red")
            self.file_analyze_button["state"] = "disabled"
            self.column_combo["state"] = "disabled"
            self.open_stats_button["state"] = "disabled"
    
    def load_emotion_model(self):
        """감정 분석 모델 로드"""
        try:
            # 현재 스크립트 실행 경로 가져오기
            initial_dir = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
            
            # 파일 선택 대화상자
            model_path = filedialog.askopenfilename(
                title="감정 분석 모델 파일 선택",
                filetypes=[("KOTE 모델", "*.bin"), ("모든 파일", "*.*")],
                initialdir=initial_dir
            )
            
            if model_path:
                # 디바이스 설정
                device = setup_device()
                
                # 모델 로드 - load_custom_model 함수 사용
                self.model = load_custom_model(model_path, device)
                self.analyze_enabled = True
                
                # 컨트롤 활성화
                self.toggle_analyze_controls(True)
                
                # 작업 기록
                log_work(
                    "모델_로드", 
                    datetime.now(), 
                    datetime.now(), 
                    파일명=os.path.basename(model_path)
                )
                
                # 상태 메시지 업데이트
                messagebox.showinfo("모델 로드", "감정 분석 모델이 성공적으로 로드되었습니다.")
        
        except Exception as e:
            error_msg = f"모델 로드 중 오류 발생: {str(e)}"
            messagebox.showerror("모델 로드 오류", error_msg)
            print(error_msg)
            traceback.print_exc()
            self.analyze_enabled = False
            self.toggle_analyze_controls(False)
    
    def analyze_direct_input(self):
        """텍스트 직접 입력 분석"""
        if not self.analyze_enabled:
            messagebox.showerror("분석 오류", "먼저 감정 분석 모델을 로드하세요.")
            return
        
        # 입력 텍스트 가져오기
        input_text = self.input_text.get(1.0, tk.END).strip()
        
        if not input_text:
            messagebox.showwarning("입력 오류", "분석할 텍스트를 입력하세요.")
            return
        
        try:
            # 텍스트 분석 실행
            result = analyze_text(input_text, self.model)
            
            # 결과 표시
            self.result_text.config(state="normal")
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, result)
            self.result_text.config(state="disabled")
            
        except Exception as e:
            error_msg = f"텍스트 분석 중 오류 발생: {str(e)}"
            messagebox.showerror("분석 오류", error_msg)
            print(error_msg)
            traceback.print_exc()
    
    def select_file(self):
        """파일 선택"""
        # 현재 스크립트 실행 경로 가져오기
        initial_dir = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
        
        # 파일 선택 대화상자
        file_path = filedialog.askopenfilename(
            title="분석할 파일 선택",
            filetypes=[("CSV 파일", "*.csv"), ("Excel 파일", "*.xlsx"), ("모든 파일", "*.*")],
            initialdir=initial_dir
        )
        
        if file_path:
            self.file_path = file_path
            # 파일 라벨 업데이트
            self.file_label.config(text=f"선택된 파일: {os.path.basename(file_path)}")
            
            try:
                # 파일 로드
                df, file_info = load_file(file_path)
                self.loaded_data = df
                self.columns = list(df.columns)
                
                # 컬럼 선택 콤보박스 업데이트
                self.column_combo["values"] = self.columns
                self.column_combo.current(0)  # 첫 번째 컬럼 선택
                self.column_combo["state"] = "readonly"
                
                # 파일 분석 버튼 활성화
                self.file_analyze_button["state"] = "normal"
                
                # 파일 정보 표시
                self.file_info_text.config(state="normal")
                self.file_info_text.delete(1.0, tk.END)
                self.file_info_text.insert(tk.END, file_info)
                self.file_info_text.config(state="disabled")
                
            except Exception as e:
                error_msg = f"파일 로드 중 오류 발생: {str(e)}"
                messagebox.showerror("파일 로드 오류", error_msg)
                print(error_msg)
                traceback.print_exc()
    
    def analyze_file(self):
        """파일 감정 분석"""
        if not self.analyze_enabled:
            messagebox.showerror("분석 오류", "먼저 감정 분석 모델을 로드하세요.")
            return
        
        if self.loaded_data is None:
            messagebox.showwarning("파일 오류", "먼저 분석할 파일을 선택하세요.")
            return
        
        # 선택된 컬럼
        selected_column = self.column_combo.get()
        
        if not selected_column:
            messagebox.showwarning("컬럼 오류", "분석할 컬럼을 선택하세요.")
            return
        
        try:
            # 파일 감정 분석 실행
            results, result_text, original_df = analyze_file(
                self.loaded_data, 
                selected_column, 
                self.model, 
                file_path=self.file_path
            )
            
            # 분석 결과 설정
            self.analyzed_data = results
            
            # 메타데이터 설정 (이미 analyze_file 내에서 처리됨)
            if not hasattr(self.analyzed_data, '_metadata'):
                self.analyzed_data._metadata = {'analysis_file_path': self.file_path}
            
            # 결과 텍스트 표시
            self.result_text.config(state="normal")
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, result_text)
            self.result_text.config(state="disabled")
            
            # 통계 버튼 활성화
            self.open_stats_button["state"] = "normal"
            
            # 통계 요약 업데이트
            self.update_stats_summary()
            
        except Exception as e:
            error_msg = f"파일 분석 중 오류 발생: {str(e)}"
            messagebox.showerror("분석 오류", error_msg)
            print(error_msg)
            traceback.print_exc()
    
    def load_analysis_result_file(self):
        """감정 분석 결과 파일 불러오기"""
        # 모델이 로드되지 않았으면 경고
        if not self.analyze_enabled:
            messagebox.showwarning("모델 미로드", "먼저 감정 분석 모델을 로드해주세요.")
            return
        
        # 파일 선택 대화상자 표시
        file_path = filedialog.askopenfilename(
            title="감정 분석 결과 파일 선택",
            filetypes=[("CSV 파일", "*.csv"), ("Excel 파일", "*.xlsx"), ("모든 파일", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            # 파일 확장자에 따라 로드 방식 결정
            _, ext = os.path.splitext(file_path)
            if ext.lower() == '.csv':
                df = pd.read_csv(file_path, encoding='utf-8-sig')
            elif ext.lower() in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            else:
                messagebox.showerror("파일 오류", "지원되지 않는 파일 형식입니다.")
                return
            
            # 필수 열이 있는지 확인
            required_columns = ['주요_감정', '감정_강도', '감정_분류']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                messagebox.showerror("파일 오류", 
                                    f"필수 열이 없습니다: {', '.join(missing_columns)}\n"
                                    f"올바른 감정 분석 결과 파일을 선택해주세요.")
                return
            
            # 메타데이터에 파일 경로 추가
            df._metadata = {"analysis_file_path": file_path}
            
            # 분석 결과 데이터프레임 초기화
            self.load_analysis_result_from_df(df)
            
        except Exception as e:
            error_msg = f"파일 로드 중 오류 발생: {str(e)}"
            messagebox.showerror("파일 로드 오류", error_msg)
            print(error_msg)
            traceback.print_exc()
    
    def load_analysis_result_from_df(self, df):
        """감정 분석 결과 데이터프레임 초기화"""
        self.analyzed_data = df
        
        # 파일 경로 정보 (있는 경우)
        file_path = getattr(df, '_metadata', {}).get('analysis_file_path', "분석 결과")
        
        # 파일 라벨 업데이트
        self.stats_file_label.config(text=f"분석 결과 파일: {os.path.basename(file_path)}")
        
        # 파일 정보 업데이트
        self.file_info_text.config(state="normal")
        self.file_info_text.delete(1.0, tk.END)
        
        info_text = f"파일 정보: {file_path}\n"
        info_text += f"총 데이터 수: {len(df)}개\n"
        info_text += f"컬럼 수: {len(df.columns)}개\n"
        
        self.file_info_text.insert(tk.END, info_text)
        self.file_info_text.config(state="disabled")
        
        # 통계 요약 업데이트
        self.update_stats_summary()
        
        # 통계 버튼 활성화
        self.open_stats_button["state"] = "normal"
    
    def update_stats_summary(self):
        """통계 요약 업데이트"""
        if self.analyzed_data is None:
            return
        
        # 통계 계산
        total_rows = len(self.analyzed_data)
        
        # 감정 분류별 통계
        try:
            # 필요한 컬럼들이 있는지 확인
            if '감정_분류' not in self.analyzed_data.columns:
                self.stats_summary_area.config(state="normal")
                self.stats_summary_area.delete(1.0, tk.END)
                self.stats_summary_area.insert(tk.END, "감정_분류 컬럼을 찾을 수 없습니다.")
                self.stats_summary_area.config(state="disabled")
                return
                
            polarity_counts = self.analyzed_data['감정_분류'].value_counts()
            polarity_percent = self.analyzed_data['감정_분류'].value_counts(normalize=True) * 100
            
            # 주요 감정별 통계 
            emotion_counts = self.analyzed_data['주요_감정'].value_counts()
            emotion_percent = self.analyzed_data['주요_감정'].value_counts(normalize=True) * 100
            
            # 통계 요약 텍스트 생성
            result_text = f"감정 분석 통계 요약 (총 {total_rows}개 항목)\n\n"
            
            # 감정 분류별 통계 (기존 형식 유지)
            result_text += "[감정 분류별 통계]\n"
            result_text += "-" * 40 + "\n"
            
            for polarity in ['긍정', '부정', '중립']:
                count = polarity_counts.get(polarity, 0)
                percent = polarity_percent.get(polarity, 0)
                result_text += f"{polarity}: {count}개 ({percent:.2f}%)\n"
            
            result_text += "-" * 40 + "\n\n"
            
            # 주요 감정별 통계 (모든 감정 표시)
            result_text += "[주요 감정별 통계]\n"
            result_text += "-" * 40 + "\n"
            
            # 모든 감정을 빈도순으로 정렬
            sorted_emotions = emotion_counts.sort_values(ascending=False)
            
            # 모든 감정에 대한 통계 표시
            for emotion, count in sorted_emotions.items():
                percent = emotion_percent[emotion]
                result_text += f"{emotion}: {count}개 ({percent:.2f}%)\n"
            
            result_text += "-" * 40 + "\n\n"
            
            # 모든 감정 점수 평균 통계
            result_text += "[감정별 평균 점수]\n"
            result_text += "-" * 40 + "\n"
            
            # 모든 감정 컬럼 찾기 (주요_감정, 감정_분류, 감정_강도를 제외한 나머지)
            emotion_columns = [col for col in self.analyzed_data.columns 
                              if col not in ['주요_감정', '감정_분류', '감정_강도', '텍스트'] 
                              and col in LABELS + ['무감정']]
            
            if emotion_columns:
                # 감정 점수 평균
                emotion_means = self.analyzed_data[emotion_columns].mean().sort_values(ascending=False)
                
                for emotion, mean_score in emotion_means.items():
                    result_text += f"{emotion}: {mean_score:.4f}\n"
            else:
                result_text += "감정 점수 컬럼을 찾을 수 없습니다.\n"
            
            result_text += "-" * 40 + "\n\n"
            
            result_text += "* 통계 분석 창을 열어 더 자세한 분석을 수행할 수 있습니다."
            
            # 결과 표시
            self.stats_summary_area.config(state="normal")
            self.stats_summary_area.delete(1.0, tk.END)
            self.stats_summary_area.insert(tk.END, result_text)
            self.stats_summary_area.config(state="disabled")
        
        except Exception as e:
            error_msg = f"통계 요약 생성 중 오류 발생: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            
            self.stats_summary_area.config(state="normal")
            self.stats_summary_area.delete(1.0, tk.END)
            self.stats_summary_area.insert(tk.END, f"통계 요약을 생성할 수 없습니다: {str(e)}")
            self.stats_summary_area.config(state="disabled")
    
    def open_statistics_window(self):
        """통계 분석 창 열기"""
        if self.analyzed_data is None:
            messagebox.showwarning("통계 오류", "먼저 감정 분석 결과 파일을 불러오세요.")
            return
        
        # 통계 창 열기
        try:
            # 분석 결과 데이터의 복사본을 전달하여 원본 데이터 보존
            copied_data = self.analyzed_data.copy()
            
            # 파일 경로 정보
            file_path = ""
            
            # 메타데이터가 있으면 복사
            if hasattr(self.analyzed_data, '_metadata') and self.analyzed_data._metadata:
                # 메타데이터를 새 사전으로 복사
                copied_data._metadata = dict(self.analyzed_data._metadata)
                # 파일 경로 가져오기
                file_path = copied_data._metadata.get('analysis_file_path', "")
            else:
                # 메타데이터가 없는 경우 기본값 설정
                copied_data._metadata = {'analysis_file_path': self.file_path or ""}
                file_path = self.file_path or ""
            
            # 통계 창 열기 (파일명 파라미터 전달)
            stats_window = load_and_display_statistics(self.parent, copied_data, file_path)
            
        except Exception as e:
            error_msg = f"통계 분석 창 열기 중 오류 발생: {str(e)}"
            messagebox.showerror("통계 오류", error_msg)
            print(error_msg)
            traceback.print_exc() 