"""
통계 분석을 위한 모델 클래스 모듈
"""
import pandas as pd
import numpy as np
import os
from datetime import datetime
import traceback
import logging

from .utils import get_group_statistics, create_intensity_bins, crosstab_with_default_columns

logger = logging.getLogger(__name__)

# 감정 분류별 극성 매핑
EMOTION_POLARITY = {
    # 긍정 감정
    '기쁨': '긍정',
    '행복': '긍정',
    '환영/호의': '긍정',
    '안심/신뢰': '긍정',
    '만족/감사': '긍정',
    
    # 부정 감정
    '슬픔': '부정',
    '분노': '부정',
    '불평/불만': '부정',
    '공포/불안': '부정',
    '혐오/싫어함': '부정',
    
    # 중립 감정
    '놀람': '중립',
    '무감정': '중립',
    '기타': '중립',
    '없음': '중립'
}

class StatisticsModel:
    """통계 분석 모델 클래스
    
    감정 분석 데이터에 대한 다양한 통계 분석 기능을 제공합니다.
    """
    
    def __init__(self):
        """모델 초기화"""
        pass
    
    def validate_data(self, df):
        """데이터 유효성 검사
        
        Args:
            df (pd.DataFrame): 검사할 데이터프레임
            
        Returns:
            bool: 데이터가 유효하면 True, 그렇지 않으면 False
        """
        # 필수 열이 있는지 확인
        required_columns = ['감정_분류', '감정_강도']
        return all(col in df.columns for col in required_columns)
    
    def analyze_overall_statistics(self, df, value_column='감정_강도'):
        """전체 통계 분석
        
        Args:
            df (pd.DataFrame): 분석할 데이터프레임
            value_column (str): 값 열 이름
            
        Returns:
            pd.DataFrame: 통계 요약 데이터프레임
        """
        # 기본 통계량 계산
        stats = df[value_column].describe()
        
        # 중앙값, 분산, 최빈값 추가
        stats['median'] = df[value_column].median()
        stats['var'] = df[value_column].var()
        stats['mode'] = df[value_column].mode()[0] if not df[value_column].mode().empty else np.nan
        
        # 통계량 순서 조정 및 반올림
        stats = pd.DataFrame({
            '통계량': [
                '개수', '평균', '표준편차', '최소값', '25%', '중앙값', '75%', '최대값', '분산', '최빈값'
            ],
            value_column: [
                stats['count'],
                round(stats['mean'], 2),
                round(stats['std'], 2),
                round(stats['min'], 2),
                round(stats['25%'], 2),
                round(stats['median'], 2),
                round(stats['75%'], 2),
                round(stats['max'], 2),
                round(stats['var'], 2),
                round(stats['mode'], 2)
            ]
        })
        
        # 인덱스 설정 및 컬럼 이름 변경
        stats = stats.set_index('통계량')
        stats.columns = [f"{value_column} 통계량"]
        
        return stats
    
    def analyze_emotion_distribution(self, df):
        """감정 분류별 분포 분석
        
        Args:
            df (pd.DataFrame): 분석할 데이터프레임
            
        Returns:
            tuple: (빈도 데이터프레임, 비율 데이터프레임)
        """
        # 주요 감정 추출 (필요한 경우)
        if '주요_감정' not in df.columns and '감정_분류' in df.columns:
            df['주요_감정'] = df['감정_분류'].apply(lambda x: x.split('_')[0] if pd.notna(x) else '무감정')
        
        # 감정 분류별 빈도 계산
        emotion_counts = pd.crosstab(
            index=df['주요_감정'] if '주요_감정' in df.columns else df['감정_분류'],
            columns='빈도',
            values=df['감정_강도'],
            aggfunc='count'
        ).reset_index()
        
        emotion_counts.columns = ['감정 분류', '빈도']
        emotion_counts['비율(%)'] = round(emotion_counts['빈도'] / emotion_counts['빈도'].sum() * 100, 1)
        
        # 정렬 및 합계 추가
        emotion_counts = emotion_counts.sort_values('빈도', ascending=False)
        total_row = pd.DataFrame({
            '감정 분류': ['합계'],
            '빈도': [emotion_counts['빈도'].sum()],
            '비율(%)': [100.0]
        })
        emotion_counts = pd.concat([emotion_counts, total_row], ignore_index=True)
        
        # 인덱스 설정
        emotion_counts = emotion_counts.set_index('감정 분류')
        
        # 빈도 및 비율 데이터프레임 생성
        counts_df = emotion_counts[['빈도']].copy()
        percents_df = emotion_counts[['비율(%)']].copy()
        
        # 컬럼명 변경
        counts_df.columns = ['합계']
        percents_df.columns = ['합계']
        
        return counts_df, percents_df
    
    def analyze_intensity_distribution(self, df):
        """감정 강도 구간별 분포 분석
        
        Args:
            df (pd.DataFrame): 분석할 데이터프레임
            
        Returns:
            pd.DataFrame: 구간별 빈도 및 비율 데이터프레임
        """
        # 감정 강도 구간화
        binned, counts, percents = create_intensity_bins(df)
        
        # 결과 데이터프레임 생성
        result = pd.DataFrame({
            '감정 강도 구간': counts.index,
            '빈도': counts.values,
            '비율(%)': percents.values.round(1)
        })
        
        # 합계 행 추가
        total_row = pd.DataFrame({
            '감정 강도 구간': ['합계'],
            '빈도': [counts.sum()],
            '비율(%)': [100.0]
        })
        result = pd.concat([result, total_row], ignore_index=True)
        
        # 인덱스 설정
        result = result.set_index('감정 강도 구간')
        
        return result
    
    def analyze_grouped_statistics(self, df, group_columns, value_column='감정_강도'):
        """그룹별 통계 분석
        
        Args:
            df (pd.DataFrame): 분석할 데이터프레임
            group_columns (list): 그룹핑 열 이름 목록
            value_column (str): 값 열 이름
            
        Returns:
            pd.DataFrame: 그룹별 통계 데이터프레임
        """
        try:
            # 데이터 타입 확인 (문자열인 경우 빈도분석만 수행)
            if value_column not in df.columns:
                print(f"경고: 분석 대상 컬럼 '{value_column}'이 데이터프레임에 존재하지 않습니다. 기본 컬럼으로 대체합니다.")
                value_column = '감정_강도'  # 기본값으로 대체
            
            # 그룹별 통계 계산
            result = get_group_statistics(df, group_columns, value_column)
            
            # 컬럼명 변경 (가독성 향상)
            col_rename = {'count': '개수'}
            
            # 숫자형 데이터인 경우 추가 통계량 컬럼명도 변경
            if 'mean' in result.columns:
                col_rename.update({
                    'mean': '평균',
                    'std': '표준편차',
                    'min': '최소값',
                    'max': '최대값',
                    'median': '중앙값'
                })
            
            result = result.rename(columns=col_rename)
            
            return result
            
        except Exception as e:
            print(f"그룹별 통계 분석 중 오류 발생: {str(e)}")
            print(traceback.format_exc())
            
            # 오류 발생 시 최소한의 결과 반환
            empty_result = pd.DataFrame(columns=group_columns + ['개수'])
            return empty_result
    
    def create_multi_level_crosstab(self, df, group_cols, value_col, normalize=False):
        """다단계 크로스탭 생성
        
        Args:
            df (pd.DataFrame): 데이터프레임
            group_cols (list): 그룹 컬럼 목록
            value_col (str): 값 컬럼
            normalize (bool, optional): 정규화 여부. Defaults to False.
            
        Returns:
            pd.DataFrame: 다단계 크로스탭
        """
        if not group_cols or len(group_cols) == 0:
            logger.warning("그룹 컬럼이 지정되지 않았습니다.")
            return pd.DataFrame()
            
        if value_col not in df.columns:
            logger.warning(f"값 컬럼 '{value_col}'이 데이터프레임에 존재하지 않습니다.")
            return pd.DataFrame()
            
        try:
            # 그룹 컬럼이 하나인 경우
            if len(group_cols) == 1:
                # 크로스탭 생성
                crosstab = pd.crosstab(df[group_cols[0]], df[value_col], margins=True, margins_name="합계")
                
                # 정규화 (행 기준)
                if normalize:
                    # 합계 행/열 제외하고 정규화
                    row_sums = crosstab.loc[:, "합계"]
                    crosstab_norm = crosstab.div(row_sums, axis=0) * 100
                    
                    # 퍼센트 소수점 1자리로 반올림
                    crosstab_norm = crosstab_norm.round(1)
                    
                    # 합계 열은 100%로 설정
                    crosstab_norm.loc[:, "합계"] = 100.0
                    
                    return crosstab_norm
                
                return crosstab
            else:
                # 그룹 컬럼이 여러 개인 경우
                # 다단계 인덱스로 크로스탭 생성
                crosstab = pd.crosstab(
                    [df[col] for col in group_cols], 
                    df[value_col], 
                    margins=True, 
                    margins_name="합계"
                )
                
                # 정규화 (행 기준)
                if normalize:
                    # 합계 열 기준으로 정규화
                    row_sums = crosstab.loc[:, "합계"]
                    crosstab_norm = crosstab.div(row_sums, axis=0) * 100
                    
                    # 퍼센트 소수점 1자리로 반올림
                    crosstab_norm = crosstab_norm.round(1)
                    
                    # 합계 열은 100%로 설정
                    crosstab_norm.loc[:, "합계"] = 100.0
                    
                    return crosstab_norm
                
                return crosstab
        except Exception as e:
            logger.error(f"다단계 크로스탭 생성 중 오류 발생: {str(e)}")
            return pd.DataFrame()
            
    def create_emotion_heatmap_data(self, df, group_cols=None):
        """감정 분류별 히트맵 데이터 생성
        
        Args:
            df (pd.DataFrame): 데이터프레임
            group_cols (list, optional): 그룹 컬럼 목록. Defaults to None.
            
        Returns:
            dict: 히트맵 데이터
        """
        try:
            result = {}
            
            # 감정 분류 컬럼 확인
            emotion_col = '감정_분류'
            if emotion_col not in df.columns:
                emotion_col = '주요_감정'
                if emotion_col not in df.columns:
                    return {'error': '감정 분류 컬럼이 존재하지 않습니다.'}
            
            # 전체 데이터에 대한 히트맵 데이터 생성
            result['overall'] = self._create_emotion_heatmap_for_group(df, emotion_col)
            
            # 그룹별 히트맵 데이터 생성 (그룹 컬럼이 지정된 경우)
            if group_cols and len(group_cols) > 0:
                # 그룹별 데이터 처리
                for col in group_cols:
                    if col not in df.columns:
                        continue
                        
                    # 고유값 목록 가져오기
                    unique_values = df[col].unique()
                    
                    # 각 고유값에 대한 히트맵 데이터 생성
                    for value in unique_values:
                        # 해당 값을 가진 데이터 필터링
                        filtered_df = df[df[col] == value]
                        
                        # 히트맵 데이터 생성
                        group_key = f"{col}: {value}"
                        result[group_key] = self._create_emotion_heatmap_for_group(filtered_df, emotion_col)
                        
                # 다단계 그룹핑 처리 (그룹 컬럼이 2개 이상인 경우)
                if len(group_cols) >= 2:
                    # 그룹별 데이터 프레임 생성
                    grouped = df.groupby(group_cols)
                    
                    # 각 그룹에 대한 히트맵 데이터 생성
                    for name, group_df in grouped:
                        # 그룹 이름 생성 (튜플인 경우 문자열로 변환)
                        if isinstance(name, tuple):
                            group_key = " / ".join([f"{col}: {val}" for col, val in zip(group_cols, name)])
                        else:
                            group_key = f"{group_cols[0]}: {name}"
                            
                        # 히트맵 데이터 생성
                        result[group_key] = self._create_emotion_heatmap_for_group(group_df, emotion_col)
            
            return result
        except Exception as e:
            logger.error(f"감정 히트맵 데이터 생성 중 오류 발생: {str(e)}")
            return {'error': f'감정 히트맵 데이터 생성 중 오류 발생: {str(e)}'}
            
    def _create_emotion_heatmap_for_group(self, df, emotion_col):
        """특정 그룹에 대한 감정 히트맵 데이터 생성
        
        Args:
            df (pd.DataFrame): 데이터프레임
            emotion_col (str): 감정 분류 컬럼
            
        Returns:
            dict: 히트맵 데이터
        """
        # 결과 딕셔너리 초기화
        result = {
            'total_count': len(df),
            'emotion_counts': {},
            'main_emotion_counts': {},
            'polarity_counts': {
                '긍정': 0,
                '중립': 0,
                '부정': 0
            },
            'polarity_percentages': {
                '긍정': 0.0,
                '중립': 0.0,
                '부정': 0.0
            }
        }
        
        if result['total_count'] == 0:
            return result
            
        # 감정 분류별 카운트
        emotion_counts = df[emotion_col].value_counts().to_dict()
        result['emotion_counts'] = emotion_counts
        
        # 주요 감정 컬럼이 있는 경우
        if '주요_감정' in df.columns and emotion_col != '주요_감정':
            main_emotion_counts = df['주요_감정'].value_counts().to_dict()
            result['main_emotion_counts'] = main_emotion_counts
        
        # 극성별 카운트 계산
        for emotion, count in emotion_counts.items():
            polarity = EMOTION_POLARITY.get(emotion, '중립')
            result['polarity_counts'][polarity] += count
        
        # 극성별 비율 계산
        for polarity in result['polarity_counts'].keys():
            count = result['polarity_counts'][polarity]
            percentage = (count / result['total_count']) * 100 if result['total_count'] > 0 else 0.0
            result['polarity_percentages'][polarity] = round(percentage, 1)
        
        return result
    
    def save_results_to_excel(self, results, output_path, group_columns=None, target_column='감정_강도'):
        """분석 결과를 Excel 파일로 저장
        
        Args:
            results (dict): 결과 데이터프레임 딕셔너리
            output_path (str): 출력 파일 경로
            group_columns (list): 그룹핑 열 이름 목록
            target_column (str): 값 열 이름
            
        Returns:
            str: 저장된 파일 경로
        """
        try:
            # Excel 작성기 생성
            writer = pd.ExcelWriter(output_path, engine='xlsxwriter')
            
            # 전체 통계 시트
            if 'overall_stats' in results:
                results['overall_stats'].to_excel(writer, sheet_name='전체_통계_요약')
            
            # 감정 분류별 통계 시트
            if 'emotion_counts' in results and 'emotion_percents' in results:
                combined_df = pd.concat([
                    results['emotion_counts'], 
                    results['emotion_percents'].rename(columns={'합계': '비율(%)'})
                ], axis=1)
                combined_df.to_excel(writer, sheet_name='감정_분류_통계')
            
            # 그룹별 통계 시트
            if 'group_stats' in results:
                results['group_stats'].to_excel(writer, sheet_name='그룹별_통계')
                
                # 시트 이름 생성
                group_name = '_'.join(group_columns) if group_columns else '그룹'
                sheet_name = f"{group_name}_통계"
                
                # 이름이 너무 길면 잘라내기 (Excel 시트 이름 제한)
                if len(sheet_name) > 31:
                    sheet_name = sheet_name[:28] + '...'
                
                # 그룹별 통계 시트로 저장
                results['group_stats'].to_excel(writer, sheet_name=sheet_name)
            
            # 다단계 빈도표 시트
            if 'multi_crosstab' in results:
                results['multi_crosstab'].to_excel(writer, sheet_name='다단계_빈도표')
            
            # 메타데이터 시트
            metadata = pd.DataFrame({
                '항목': [
                    '분석 날짜',
                    '분석 대상 컬럼',
                    '그룹 컬럼'
                ],
                '값': [
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    target_column,
                    ', '.join(group_columns) if group_columns else '없음'
                ]
            })
            metadata.to_excel(writer, sheet_name='메타데이터', index=False)
            
            # 저장
            writer.close()
            
            return output_path
        
        except Exception as e:
            print(f"Excel 저장 중 오류 발생: {str(e)}")
            print(traceback.format_exc())
            raise 