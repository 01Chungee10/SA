"""
통계 분석 모델과 뷰를 연결하는 컨트롤러 모듈
"""
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import pandas as pd
import traceback
import logging

from .model import StatisticsModel
from .view import StatisticsView
from .utils import format_file_name, ensure_output_dir

logger = logging.getLogger(__name__)

class StatisticsController:
    """통계 분석 컨트롤러 클래스
    
    Model과 View를 연결하고 사용자 상호작용을 처리합니다.
    """
    
    def __init__(self, master=None, df=None, filename=None):
        """컨트롤러 초기화
        
        Args:
            master: 부모 윈도우, None이면 새 창 생성
            df (pd.DataFrame, optional): 분석할 데이터프레임
            filename (str, optional): 데이터 파일명
        """
        # Toplevel 생성 (필요한 경우)
        if master is None:
            self.window = tk.Tk()
        else:
            self.window = tk.Toplevel(master)
        
        # 뷰 생성
        self.view = StatisticsView(self.window)
        
        # 모델 생성
        self.model = StatisticsModel()
        
        # 데이터 설정
        self.df = df
        self.filename = filename or "[데이터프레임]"
        
        # 결과 데이터
        self.results = {}
        
        # 분석에 필요한 컬럼 정보 (감정_분류, 주요_감정, 감정_강도)
        self.required_columns = ['감정_분류', '주요_감정', '감정_강도']
        
        # 이벤트 핸들러 설정
        self.setup_event_handlers()
        
        # 데이터 로드 (있는 경우)
        if df is not None:
            self.initialize_data(df, filename)
    
    def setup_event_handlers(self):
        """이벤트 핸들러 설정"""
        # 그룹 컬럼 추가 버튼
        self.view.add_column_button.config(command=self.add_group_column)
        
        # 그룹 컬럼 제거 버튼
        self.view.remove_column_button.config(command=self.remove_group_column)
        
        # 그룹 분석 실행 버튼
        self.view.run_analysis_button.config(command=self.run_analysis)
        
        # 결과 저장 버튼
        self.view.save_results_button.config(command=self.save_results)
        
        # 이벤트 연결
        self.view.set_on_run_callback(self.run_analysis)
        self.view.set_on_move_up_callback(self.move_up_selected_column)
        self.view.set_on_move_down_callback(self.move_down_selected_column)
        self.view.set_on_add_callback(self.add_selected_column)
        self.view.set_on_remove_callback(self.remove_selected_column)
    
    def initialize_data(self, df, filename=None):
        """데이터 초기화
        
        Args:
            df (pd.DataFrame): 분석할 데이터프레임
            filename (str, optional): 데이터 파일명
        """
        try:
            # 데이터 유효성 검사
            if not self.model.validate_data(df):
                self.view.show_error("데이터 오류", "데이터에 필요한 열(감정_분류, 감정_강도)이 없습니다.")
                return
            
            # 데이터 설정
            self.df = df
            self.filename = filename or "[데이터프레임]"
            
            # 파일 정보 업데이트
            self.view.update_file_info(
                os.path.basename(self.filename) if os.path.isfile(self.filename) else self.filename,
                len(df),
                len(df.columns)
            )
            
            # 컬럼 목록 업데이트
            available_columns = list(df.columns)
            self.view.update_available_columns(available_columns)
            
            # 상태 메시지 업데이트
            self.view.info_message("데이터 로드 완료. 그룹 컬럼을 선택하고 분석을 실행하세요.")
        
        except Exception as e:
            self.view.show_error("초기화 오류", f"데이터 초기화 중 오류 발생: {str(e)}")
            print(traceback.format_exc())
    
    def add_group_column(self):
        """선택한 컬럼을 그룹 컬럼 목록에 추가"""
        columns = self.view.get_selected_available_column()
        
        if columns:
            # 이미 선택된 컬럼 목록 가져오기
            selected_columns = self.view.get_selected_group_columns()
            
            # 각 선택된 컬럼에 대해 처리
            added_count = 0
            for column in columns:
                if column not in selected_columns:
                    # 그룹 컬럼 리스트박스에 추가
                    self.view.selected_columns_listbox.insert(tk.END, column)
                    added_count += 1
            
            if added_count > 0:
                self.view.info_message(f"{added_count}개 컬럼이 그룹 목록에 추가되었습니다.")
            else:
                self.view.info_message("모든 선택된 컬럼이 이미 그룹 목록에 있습니다.")
        else:
            self.view.info_message("추가할 컬럼을 선택하세요.")
    
    def remove_group_column(self):
        """선택한 컬럼을 그룹 컬럼 목록에서 제거"""
        selection = self.view.selected_columns_listbox.curselection()
        
        if selection:
            column = self.view.selected_columns_listbox.get(selection[0])
            self.view.selected_columns_listbox.delete(selection[0])
            self.view.info_message(f"'{column}' 컬럼이 그룹 목록에서 제거되었습니다.")
        else:
            self.view.info_message("제거할 그룹 컬럼을 선택하세요.")
    
    def run_analysis(self):
        """통계 분석 실행"""
        if self.df is None or self.df.empty:
            self.view.show_warning("데이터 없음", "분석할 데이터가 없습니다.")
            return
            
        # 그룹 컬럼과 대상 컬럼 가져오기
        group_columns = self.view.get_selected_group_columns()
        target_column = self.view.get_target_column()
        
        # 대상 컬럼이 비어있는 경우 기본값 설정
        if not target_column:
            if '주요_감정' in self.df.columns:
                target_column = '주요_감정'
            elif '감정_분류' in self.df.columns:
                target_column = '감정_분류'
            elif '감정_강도' in self.df.columns:
                target_column = '감정_강도'
                
        # 분석 시작 전 프로그레스바 초기화
        self.view.update_progress(0)
        
        try:
            # 데이터 검증
            valid, message = self.model.validate_data(self.df)
            if not valid:
                self.view.show_warning("데이터 검증 실패", message)
                return
                
            # 결과를 저장할 딕셔너리
            results = {}
            
            # 1. 기본 통계량 분석
            self.view.update_progress(10)
            try:
                results['overall_stats'] = self.model.analyze_overall_statistics(self.df)
            except Exception as e:
                logger.error(f"기본 통계량 분석 중 오류 발생: {str(e)}")
                results['overall_stats'] = pd.DataFrame({'오류': [f"기본 통계량 분석 실패: {str(e)}"]})
                
            # 2. 감정 분포 분석
            self.view.update_progress(30)
            try:
                emotion_counts, emotion_percents = self.model.analyze_emotion_distribution(self.df)
                results['emotion_counts'] = emotion_counts
                results['emotion_percents'] = emotion_percents
                
                # 히트맵 데이터 생성
                heatmap_data = self.model.create_emotion_heatmap_data(self.df, group_columns)
                results['heatmap_data'] = heatmap_data
            except Exception as e:
                logger.error(f"감정 분포 분석 중 오류 발생: {str(e)}")
                results['emotion_counts'] = pd.DataFrame({'오류': [f"감정 분포 분석 실패: {str(e)}"]})
                results['emotion_percents'] = pd.DataFrame({'오류': [f"감정 분포 분석 실패: {str(e)}"]})
                results['heatmap_data'] = {'error': f"히트맵 생성 실패: {str(e)}"}
                
            # 3. 감정 강도 분포 분석
            self.view.update_progress(50)
            try:
                if '감정_강도' in self.df.columns:
                    intensity_stats = self.model.analyze_intensity_distribution(self.df)
                    results['intensity_stats'] = intensity_stats
            except Exception as e:
                logger.error(f"감정 강도 분포 분석 중 오류 발생: {str(e)}")
                results['intensity_stats'] = pd.DataFrame({'오류': [f"감정 강도 분포 분석 실패: {str(e)}"]})
                
            # 4. 그룹별 통계 분석 (그룹 컬럼이 지정된 경우)
            self.view.update_progress(70)
            if group_columns:
                try:
                    # 대상 컬럼이 문자열인지 숫자인지 확인
                    if target_column in self.df.columns:
                        is_numeric = pd.api.types.is_numeric_dtype(self.df[target_column])
                        
                        if not is_numeric:
                            # 문자열 컬럼인 경우 빈도 분석만 수행
                            self.view.show_warning("문자열 컬럼", 
                                                f"'{target_column}'은 문자열 컬럼이므로 빈도 분석만 수행합니다.")
                        
                        # 그룹별 통계 분석 (숫자 컬럼인 경우에만 통계값 계산)
                        grouped_stats = self.model.analyze_grouped_statistics(
                            self.df, group_columns, target_column, numeric_only=is_numeric
                        )
                        results['grouped_stats'] = grouped_stats
                    else:
                        self.view.show_warning("컬럼 없음", f"대상 컬럼 '{target_column}'이 데이터에 존재하지 않습니다.")
                except Exception as e:
                    logger.error(f"그룹별 통계 분석 중 오류 발생: {str(e)}")
                    results['grouped_stats'] = pd.DataFrame({'오류': [f"그룹별 통계 분석 실패: {str(e)}"]})
                    
            # 5. 다단계 빈도표 분석 (그룹 컬럼이 지정된 경우)
            self.view.update_progress(90)
            if group_columns:
                try:
                    # 감정 분류 다단계 빈도표
                    if '감정_분류' in self.df.columns:
                        crosstab_emotion = self.model.create_multi_level_crosstab(
                            self.df, group_columns, '감정_분류'
                        )
                        results['crosstab_emotion'] = crosstab_emotion
                        
                        # 정규화된 빈도표 (퍼센트)
                        crosstab_emotion_pct = self.model.create_multi_level_crosstab(
                            self.df, group_columns, '감정_분류', normalize=True
                        )
                        results['crosstab_emotion_pct'] = crosstab_emotion_pct
                        
                    # 주요 감정 다단계 빈도표
                    if '주요_감정' in self.df.columns:
                        crosstab_main = self.model.create_multi_level_crosstab(
                            self.df, group_columns, '주요_감정'
                        )
                        results['crosstab_main'] = crosstab_main
                        
                        # 정규화된 빈도표 (퍼센트)
                        crosstab_main_pct = self.model.create_multi_level_crosstab(
                            self.df, group_columns, '주요_감정', normalize=True
                        )
                        results['crosstab_main_pct'] = crosstab_main_pct
                except Exception as e:
                    logger.error(f"다단계 빈도표 생성 중 오류 발생: {str(e)}")
                    results['crosstab_emotion'] = pd.DataFrame({'오류': [f"다단계 빈도표 생성 실패: {str(e)}"]})
                    results['crosstab_main'] = pd.DataFrame({'오류': [f"다단계 빈도표 생성 실패: {str(e)}"]})
                    
            # 분석 대상 컬럼 가져오기 (기본값: 감정_강도)
            target_column = self.view.get_target_column()
            
            # 분석 옵션 가져오기
            options = self.view.get_analysis_options()
            
            # 그룹 컬럼이 선택되지 않았을 경우
            if not group_columns:
                self.view.show_error("분석 오류", "그룹 컬럼을 하나 이상 선택하세요.")
                return
            
            # 타깃 컬럼의 데이터 타입 확인
            if target_column in self.df.columns:
                sample_value = self.df[target_column].dropna().head(1)
                is_numeric = True
                
                if len(sample_value) > 0:
                    val = sample_value.iloc[0]
                    if isinstance(val, str):
                        try:
                            float(val)  # 숫자로 변환 시도
                        except ValueError:
                            is_numeric = False
                            # 문자열 컬럼인 경우 경고 메시지
                            self.view.show_warning(
                                "문자열 컬럼 선택됨", 
                                f"선택한 컬럼 '{target_column}'은 문자열 값('{val}')을 포함하고 있어 빈도 분석만 수행됩니다."
                            )
            
            # 결과 저장 변수
            results = {}
            
            # 진행 상태 표시
            self.view.info_message("그룹 분석을 실행하는 중입니다...")
            self.view.update_progress(10)
            
            # 1. 기본 통계량 분석
            if options.get('basic_stats', True):
                self.view.info_message("기본 통계량 분석 중...")
                self.view.update_progress(20)
                
                try:
                    overall_stats = self.model.analyze_overall_statistics(self.df, target_column)
                    results['overall_stats'] = overall_stats
                except Exception as e:
                    print(f"기본 통계량 분석 중 오류 발생: {str(e)}")
                    results['overall_stats'] = pd.DataFrame({'오류': [f'기본 통계량 분석 실패: {str(e)}']})
            
            # 2. 감정 분포 분석
            if options.get('emotion_distribution', True):
                self.view.info_message("감정 분포 분석 중...")
                self.view.update_progress(40)
                
                try:
                    emotion_counts, emotion_percents = self.model.analyze_emotion_distribution(self.df)
                    results['emotion_counts'] = emotion_counts
                    results['emotion_percents'] = emotion_percents
                    
                    # 감정 히트맵 데이터 생성
                    heatmap_data = self.model.create_emotion_heatmap_data(self.df, group_columns)
                    results['heatmap_data'] = heatmap_data
                    
                except Exception as e:
                    print(f"감정 분포 분석 중 오류 발생: {str(e)}")
                    results['emotion_counts'] = pd.DataFrame({'오류': [f'감정 분포 분석 실패: {str(e)}']})
            
            # 3. 감정 강도 분포 분석
            if options.get('intensity_distribution', True):
                self.view.info_message("감정 강도 분포 분석 중...")
                self.view.update_progress(60)
                
                try:
                    intensity_stats = self.model.analyze_intensity_distribution(self.df)
                    results['intensity_stats'] = intensity_stats
                except Exception as e:
                    print(f"감정 강도 분포 분석 중 오류 발생: {str(e)}")
                    results['intensity_stats'] = pd.DataFrame({'오류': [f'감정 강도 분포 분석 실패: {str(e)}']})
            
            # 4. 그룹별 통계 분석
            if options.get('grouped_stats', True):
                self.view.info_message("그룹별 통계 분석 중...")
                self.view.update_progress(80)
                
                try:
                    grouped_stats = self.model.analyze_grouped_statistics(self.df, group_columns, target_column)
                    results['grouped_stats'] = grouped_stats
                except Exception as e:
                    print(f"그룹별 통계 분석 중 오류 발생: {str(e)}")
                    results['grouped_stats'] = pd.DataFrame({'오류': [f'그룹별 통계 분석 실패: {str(e)}']})
            
            # 5. 다단계 빈도표 분석
            if options.get('multi_level_crosstab', True):
                self.view.info_message("다단계 빈도표 분석 중...")
                self.view.update_progress(90)
                
                try:
                    # 감정_분류와 주요_감정 모두에 대한 다단계 빈도표 생성
                    crosstab_emotion = self.model.create_multi_level_crosstab(self.df, group_columns, '감정_분류')
                    results['crosstab_emotion'] = crosstab_emotion
                    
                    # 주요_감정에 대한 다단계 빈도표 생성
                    if '주요_감정' in self.df.columns:
                        crosstab_main = self.model.create_multi_level_crosstab(self.df, group_columns, '주요_감정')
                        results['crosstab_main'] = crosstab_main
                        
                except Exception as e:
                    print(f"다단계 빈도표 분석 중 오류 발생: {str(e)}")
                    print(traceback.format_exc())
                    results['crosstab_emotion'] = pd.DataFrame({'오류': [f'다단계 빈도표 분석 실패: {str(e)}']})
            
            # 결과 저장 및 표시
            self.results = results
            self.view.display_results(results)
            self.view.update_progress(100)
            self.view.info_message("그룹 분석이 완료되었습니다.")
            
        except Exception as e:
            self.view.show_error("분석 오류", f"그룹 분석 중 오류가 발생했습니다: {str(e)}")
            print(f"그룹 분석 중 오류 발생: {str(e)}")
            print(traceback.format_exc())
    
    def save_results(self):
        """분석 결과 저장"""
        if not self.results:
            self.view.show_error("저장 오류", "저장할 분석 결과가 없습니다.")
            return
        
        try:
            # 출력 디렉토리 확인
            output_dir = ensure_output_dir()
            
            # 파일명 생성
            base_filename = os.path.basename(self.filename) if os.path.isfile(self.filename) else "통계분석"
            output_filename = format_file_name(base_filename, "통계분석")
            output_path = os.path.join(output_dir, output_filename)
            
            # 결과 저장
            self.model.save_results_to_excel(
                self.results, 
                output_path, 
                self.view.get_selected_group_columns(),
                self.view.get_target_column()
            )
            
            # 성공 메시지
            self.view.show_info("저장 완료", f"분석 결과가 다음 위치에 저장되었습니다:\n{output_path}")
            self.view.info_message(f"분석 결과 저장 완료: {output_filename}")
        
        except Exception as e:
            self.view.show_error("저장 오류", f"결과 저장 중 오류 발생: {str(e)}")
            print(traceback.format_exc())

def load_and_display_statistics(parent=None, df=None, filename=None):
    """통계 분석 창 로드 및 표시
    
    Args:
        parent: 부모 윈도우
        df (pd.DataFrame, optional): 분석할 데이터프레임
        filename (str, optional): 데이터 파일명
        
    Returns:
        StatisticsController: 생성된 컨트롤러 인스턴스
    """
    controller = StatisticsController(parent, df, filename)
    return controller 