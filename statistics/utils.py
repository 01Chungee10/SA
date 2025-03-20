"""
통계 분석에 필요한 유틸리티 함수를 제공하는 모듈
"""
import pandas as pd
import numpy as np
import os
from datetime import datetime
import traceback

def format_file_name(base_name, suffix="기술통계량", timestamp=None):
    """분석 결과 파일 이름 포맷팅
    
    Args:
        base_name (str): 기본 파일명
        suffix (str): 접미사
        timestamp (datetime, optional): 타임스탬프, None이면 현재 시간 사용
        
    Returns:
        str: 포맷팅된 파일명
    """
    # 타임스탬프 생성
    if timestamp is None:
        timestamp = datetime.now()
    
    timestamp_str = timestamp.strftime("%Y%m%d%H%M%S")
    
    # 파일 확장자 제거
    base_name = os.path.splitext(os.path.basename(base_name))[0]
    
    return f"{base_name}_{suffix}_{timestamp_str}.xlsx"

def ensure_output_dir(base_dir=None):
    """출력 디렉토리 확보
    
    Args:
        base_dir (str, optional): 기본 디렉토리 경로, None이면 현재 디렉토리 사용
        
    Returns:
        str: 출력 디렉토리 경로
    """
    if base_dir is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 상위 디렉토리로 이동 (statistics 폴더에서 감정분석 폴더로)
    parent_dir = os.path.dirname(base_dir)
    
    # 출력 디렉토리 경로
    output_dir = os.path.join(parent_dir, "output")
    
    # 디렉토리가 없으면 생성
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    return output_dir

def get_group_statistics(df, group_columns, value_column, agg_funcs=None):
    """그룹별 통계 계산
    
    Args:
        df (pd.DataFrame): 데이터프레임
        group_columns (list): 그룹핑 열 이름 목록
        value_column (str): 값 열 이름
        agg_funcs (dict, optional): 집계 함수 딕셔너리, None이면 기본값 사용
        
    Returns:
        pd.DataFrame: 그룹별 통계 데이터프레임
    """
    # 값 컬럼 데이터 타입 확인
    if value_column not in df.columns:
        raise ValueError(f"컬럼 '{value_column}'이 데이터프레임에 존재하지 않습니다.")
    
    # 문자열 데이터 확인
    data_sample = df[value_column].dropna().head(1)
    is_numeric = True
    
    if len(data_sample) > 0:
        sample_val = data_sample.iloc[0]
        is_numeric = isinstance(sample_val, (int, float, np.number))
        
        # 값이 문자열인 경우, 숫자로 변환 가능한지 확인
        if isinstance(sample_val, str):
            try:
                float(sample_val)
                is_numeric = True
            except ValueError:
                is_numeric = False
    
    # 숫자형 데이터가 아닌 경우 빈도수만 계산
    if not is_numeric:
        print(f"경고: '{value_column}' 컬럼은 문자열 데이터를 포함하고 있어 빈도수 통계만 계산합니다.")
        agg_funcs = {'count': 'count'}
    else:
        # 숫자형 데이터인 경우 기본 집계 함수 사용
        if agg_funcs is None:
            agg_funcs = {
                'count': 'count',
                'mean': 'mean',
                'std': 'std',
                'min': 'min',
                'max': 'max',
                'median': lambda x: x.median()
            }
    
    try:
        # 그룹별 통계 계산
        grouped = df.groupby(group_columns)[value_column].agg(agg_funcs).reset_index()
        
        # NaN 값 처리
        grouped = grouped.fillna(0)
        
        # 소수점 두 자리로 반올림 (숫자형 데이터인 경우만)
        if is_numeric:
            for col in grouped.columns:
                if col not in group_columns and col != 'count':
                    grouped[col] = grouped[col].round(2)
        
        return grouped
    except Exception as e:
        print(f"그룹 통계 계산 중 오류 발생: {str(e)}")
        print(traceback.format_exc())
        
        # 오류 발생 시 빈 데이터프레임 반환
        empty_df = pd.DataFrame(columns=group_columns + ['count'])
        return empty_df

def create_intensity_bins(df, column='감정_강도', bins=None, labels=None):
    """감정 강도 구간화
    
    Args:
        df (pd.DataFrame): 데이터프레임
        column (str): 감정 강도 열 이름
        bins (list, optional): 구간 경계, None이면 기본값 사용
        labels (list, optional): 구간 라벨, None이면 기본값 사용
        
    Returns:
        tuple: (구간화된 시리즈, 구간별 빈도 시리즈, 구간별 비율 시리즈)
    """
    if bins is None:
        bins = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
    
    if labels is None:
        labels = ['0-0.2', '0.2-0.4', '0.4-0.6', '0.6-0.8', '0.8-1.0']
    
    # 감정 강도 구간화
    binned = pd.cut(df[column], bins=bins, labels=labels)
    
    # 구간별 빈도 및 비율 계산
    counts = binned.value_counts().sort_index()
    percents = binned.value_counts(normalize=True).sort_index() * 100
    
    return binned, counts, percents

def crosstab_with_default_columns(df, index_columns, column='감정_분류', default_columns=None):
    """기본 열이 포함된 교차표 생성
    
    Args:
        df (pd.DataFrame): 데이터프레임
        index_columns (list): 인덱스 열 목록
        column (str): 분석 열 이름
        default_columns (list, optional): 항상 포함할 열 목록, None이면 기본값 사용
        
    Returns:
        tuple: (빈도 교차표, 비율 교차표)
    """
    if default_columns is None:
        default_columns = ['긍정', '부정', '중립']
    
    # 교차표 생성
    counts = pd.crosstab(
        index=[df[col] for col in index_columns],
        columns=df[column],
        margins=True,
        margins_name='합계'
    )
    
    # 상대 빈도(퍼센트) 계산
    percents = pd.crosstab(
        index=[df[col] for col in index_columns],
        columns=df[column],
        margins=True,
        margins_name='합계',
        normalize='index'
    ) * 100
    
    # 기본 열 추가
    for col in default_columns:
        if col not in counts.columns:
            counts[col] = 0
            percents[col] = 0
    
    # 컬럼 순서 정렬
    cols = [col for col in default_columns if col in counts.columns]
    cols.append('합계')
    counts = counts[cols]
    percents = percents[cols]
    
    return counts, percents 