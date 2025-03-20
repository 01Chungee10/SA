"""
감정 분석 프로젝트의 기본 설정 및 유틸리티 함수
"""
import os
import sys
import time
import base64
import logging
from datetime import datetime, timedelta
import pandas as pd
import torch

# 파일 확장자 정의
csv_ext = ".csv"  # CSV 파일 확장자

# 로깅 설정
def setup_logging():
    """로깅 시스템 설정"""
    logging.getLogger().setLevel(logging.CRITICAL)
    print("로깅 시스템이 설정되었습니다.")

# 레이블 및 감정 맵핑 정의
LABELS = ['불평/불만', '환영/호의', '감동/감탄', '지긋지긋', '고마움', '슬픔', '화남/분노', '존경', '기대감',
          '우쭐댐/무시함', '안타까움/실망', '비장함', '의심/불신', '뿌듯함', '편안/쾌적', '신기함/관심', '아껴주는',
          '부끄러움', '공포/무서움', '절망', '한심함', '역겨움/징그러움', '짜증', '어이없음', '없음', '패배/자기혐오',
          '귀찮음', '힘듦/지침', '즐거움/신남', '깨달음', '죄책감', '증오/혐오', '흐뭇함(귀여움/예쁨)', '당황/난처',
          '경악', '부담/안_내킴', '서러움', '재미없음', '불쌍함/연민', '놀람', '행복', '불안/걱정', '기쁨', '안심/신뢰']

# 감정 극성 맵핑
POLARITY_MAP = {
    '불평/불만': '부정', '당황/난처': '부정', '짜증': '부정', '슬픔': '부정', '절망': '부정',
    '부끄러움': '부정', '재미없음': '부정', '안타까움/실망': '부정', '역겨움/징그러움': '부정', '경악': '부정',
    '부담/안_내킴': '부정', '공포/무서움': '부정', '증오/혐오': '부정', '죄책감': '부정', '불안/걱정': '부정',
    '의심/불신': '부정', '화남/분노': '부정', '패배/자기혐오': '부정', '귀찮음': '부정', '서러움': '부정',
    '지긋지긋': '부정', '어이없음': '부정', '불쌍함/연민': '부정', '한심함': '부정', '힘듦/지침': '부정',
    '감동/감탄': '긍정', '행복': '긍정', '기쁨': '긍정', '고마움': '긍정', '즐거움/신남': '긍정',
    '아껴주는': '긍정', '기대감': '긍정', '편안/쾌적': '긍정', '환영/호의': '긍정', '신기함/관심': '긍정',
    '안심/신뢰': '긍정', '존경': '긍정', '흐뭇함(귀여움/예쁨)': '긍정', '뿌듯함': '긍정',
    '우쭐댐/무시함': '중립', '놀람': '중립', '깨달음': '중립', '비장함': '중립', '없음': '중립'
}

# GPU 설정
def setup_device():
    """GPU 사용 설정 및 장치 정보 반환"""
    os.environ['CUDA_VISIBLE_DEVICES'] = '-1'  # GPU 사용 비활성화
    device = torch.device("cpu")
    print(f"사용 중인 디바이스: {device}")
    return device

# 리소스 경로 가져오기
def resource_path(relative_path):
    """실행 파일 또는 스크립트 경로 기준으로 리소스 경로 가져오기"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller가 생성한 임시 폴더
        base_path = sys._MEIPASS
    else:
        # 일반 실행 시 현재 디렉토리
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

# 출력 디렉토리 확인 및 생성
def ensure_output_dir():
    """출력 디렉토리 확인 및 생성"""
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    return output_dir

# 작업 기록 함수
def log_work(작업분류, start_time, end_time=None, 분석건수=None, 파일명=None, 기타정보=None):
    """작업 기록을 CSV 파일로 저장
    
    Args:
        작업분류 (str): 작업 유형 (텍스트_감정분석, 파일_감정분석 등)
        start_time (datetime 또는 float): 작업 시작 시간
        end_time (datetime 또는 float, optional): 작업 종료 시간
        분석건수 (int, optional): 분석한 항목 수
        파일명 (str, optional): 분석한 파일 이름
        기타정보 (str, optional): 추가 정보
    """
    if end_time is None:
        end_time = datetime.now()
    
    # datetime 객체 또는 타임스탬프(float) 처리
    if isinstance(start_time, datetime):
        작업시작시간 = start_time.strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(end_time, datetime):
            소요시간 = (end_time - start_time).total_seconds()
        else:
            현재시각 = datetime.fromtimestamp(end_time)
            소요시간 = (현재시각 - start_time).total_seconds()
    else:
        작업시작시간 = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(end_time, datetime):
            시작시각 = datetime.fromtimestamp(start_time)
            소요시간 = (end_time - 시작시각).total_seconds()
        else:
            소요시간 = end_time - start_time
    
    # 소요시간 반올림
    소요시간 = round(소요시간, 2)
    
    # 기본 데이터
    data = {
        '작업분류': [작업분류], 
        '작업시작시간': [작업시작시간], 
        '소요시간(초)': [소요시간]
    }
    
    # 추가 정보가 있으면 추가
    if 분석건수 is not None:
        data['분석건수'] = [분석건수]
    
    if 파일명 is not None:
        data['파일명'] = [파일명]
    
    if 기타정보 is not None:
        data['기타정보'] = [기타정보]
    
    record_df = pd.DataFrame(data)
    
    # output 폴더 생성 및 확인
    output_dir = ensure_output_dir()
    
    # CSV 파일로 저장
    output_filename = os.path.join(output_dir, '감정분석_작업기록.csv')
    
    # 파일 존재 여부 확인
    file_exists = os.path.isfile(output_filename)
    
    # 파일이 존재하면 추가, 아니면 새로 생성
    if file_exists:
        existing_df = pd.read_csv(output_filename, encoding='utf-8-sig')
        combined_df = pd.concat([existing_df, record_df], ignore_index=True)
        combined_df.to_csv(output_filename, index=False, encoding='utf-8-sig')
    else:
        record_df.to_csv(output_filename, index=False, encoding='utf-8-sig')
    
    return output_filename

# 스타일 설정
STYLE = """
<style>
    table.dataframe td, table.dataframe th {
        text-align: left !important;
        white-space: nowrap;
        border: 1px solid #cccccc;
    }
    table.dataframe {
        border-collapse: collapse;
    }
</style>
"""

# 모듈 초기화 함수
def init_config():
    """기본 설정 초기화"""
    # 모델 캐시 디렉토리 설정
    os.environ['TRANSFORMERS_CACHE'] = resource_path('model_cache')
    os.environ['HF_HOME'] = resource_path('model_cache')
    
    # Pandas 표시 옵션 설정
    pd.set_option('display.max_rows', 10)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', 150)
    
    # 로깅 설정
    setup_logging()
    
    # 기본 설정 완료 메시지
    print("기본 설정이 초기화되었습니다.") 