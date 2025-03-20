"""
텍스트 입력에 대한 감정 분석 기능 모듈
"""
import os
import numpy as np
import pandas as pd
from datetime import datetime
import traceback
import torch

from configure import LABELS, POLARITY_MAP, ensure_output_dir, log_work

def analyze_text(text, model, source_label="", replace_none=False):
    """
    입력된 텍스트에 대한 감정 분석 수행
    
    Args:
        text: 분석할 텍스트
        model: 감정 분석 모델 인스턴스
        source_label: 텍스트 소스 라벨 (선택사항)
        replace_none: '없음'을 '무감정'으로 대체할지 여부
        
    Returns:
        str: 분석 결과 텍스트
    """
    try:
        # 텍스트 입력 검증
        if text is None:
            return "오류: 입력 텍스트가 없습니다."
        
        # 문자열로 변환 및 공백 제거
        text = str(text).strip()
        
        if not text:
            return "오류: 입력 텍스트가 비어 있습니다."
            
        # 작업 시작 시간 기록
        analyze_start_time = datetime.now()
        
        result_text = ""
        
        # 소스 라벨이 있으면 추가
        if source_label:
            result_text += f"{source_label} 감정 분석 결과:\n\n"
        
        # 모델 추론 실행
        with torch.no_grad():
            output = model(text).cpu().numpy()[0]
        
        # 결과를 데이터프레임으로 변환
        data = {'감정': LABELS, '확률/강도': output}
        df = pd.DataFrame(data)
        
        # 확률/강도 값 기준으로 내림차순 정렬
        df_sorted = df.sort_values(by='확률/강도', ascending=False)
        
        if len(df_sorted) > 0:
            # 가장 높은 감정 표시
            top_emotion = df_sorted.iloc[0]['감정']
            top_score = df_sorted.iloc[0]['확률/강도']
            top_polarity = POLARITY_MAP.get(top_emotion, '중립')
            
            # '없음' 감정을 '무감정'으로 대체
            if replace_none and top_emotion == "없음":
                top_emotion = "무감정"
                
            # 주요 감정 표시
            result_text += f"주요 감정: {top_emotion} ({top_polarity})\n\n"
            result_text += f"감정 점수 (내림차순):\n"
            
            # 모든 감정 결과 표시 (표 형식으로)
            # 표 헤더
            table_header = f"{'감정':<20} | {'확률/강도':<10} | {'분류':<8}\n"
            table_separator = f"{'-'*20}-+-{'-'*10}-+-{'-'*8}\n"
            
            result_text += table_header
            result_text += table_separator
            
            # 모든 감정에 대한 결과 표시
            for idx, row in df_sorted.iterrows():
                emotion = row['감정']
                score = row['확률/강도']
                polarity = POLARITY_MAP.get(emotion, '중립')
                
                # '없음'을 '무감정'으로 대체
                if replace_none and emotion == "없음":
                    emotion_display = "무감정"
                else:
                    emotion_display = emotion
                
                # 표 형식으로 결과 추가
                result_text += f"{emotion_display:<20} | {score:<10.6f} | {polarity:<8}\n"
            
            # 작업 종료 시간 기록 및 작업 로그 저장
            analyze_end_time = datetime.now()
            log_work(
                "텍스트_감정분석", 
                analyze_start_time, 
                analyze_end_time,
                분석건수=1, 
                기타정보=f"주요감정: {top_emotion}, 강도: {top_score:.4f}"
            )
        
        return result_text
            
    except Exception as e:
        error_msg = f"텍스트 분석 중 오류가 발생했습니다: {str(e)}"
        print(f"텍스트 분석 중 오류 발생: {e}")
        print(traceback.format_exc())
        return error_msg

def save_analysis_result(text, preds, top_emotion, top_score, top_polarity, replace_none=False):
    """
    감정 분석 결과를 CSV 파일로 저장
    
    Args:
        text: 분석한 텍스트
        preds: 모델 예측 값
        top_emotion: 주요 감정
        top_score: 주요 감정 점수
        top_polarity: 주요 감정 분류
        replace_none: '없음'을 '무감정'으로 대체할지 여부
        
    Returns:
        str: 저장된 파일 경로 또는 None
    """
    try:
        # output 디렉토리 확인 및 생성
        output_dir = ensure_output_dir()
        
        # 타임스탬프 생성
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        result_file_name = f"텍스트_감정분석_{timestamp}.csv"
        save_path = os.path.join(output_dir, result_file_name)
        
        # 텍스트 길이 제한
        text_preview = text[:100] + "..." if len(text) > 100 else text
        
        # '없음'을 '무감정'으로 대체
        if replace_none and top_emotion == "없음":
            top_emotion = "무감정"
            
        # 결과 데이터프레임 생성
        result_data = {
            '텍스트': [text_preview],
            '주요_감정': [top_emotion],
            '감정_강도': [top_score],
            '감정_분류': [top_polarity]
        }
        
        # 모든 감정 점수 추가
        for label, score in zip(LABELS, preds):
            # 라벨이 '없음'이고 replace_none이 True이면 '무감정'으로 변경
            if replace_none and label == "없음":
                result_data["무감정"] = [score]
            else:
                result_data[label] = [score]
        
        result_df = pd.DataFrame(result_data)
        
        # 결과 저장
        result_df.to_csv(save_path, index=False, encoding='utf-8-sig')
        print(f"분석 결과가 저장되었습니다: {save_path}")
        return save_path
        
    except Exception as e:
        print(f"결과 저장 중 오류 발생: {str(e)}")
        print(traceback.format_exc())
        return None

if __name__ == "__main__":
    # 테스트용 코드
    from KOTE_load import load_model
    
    device = torch.device("cpu")
    model = load_model(device)
    
    # 샘플 텍스트로 테스트
    test_text = "오늘은 정말 행복한 하루였어요!"
    
    result_text = analyze_text(test_text, model, "테스트")
    print(result_text) 