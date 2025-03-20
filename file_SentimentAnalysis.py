"""
파일 입력에 대한 감정 분석 기능 모듈
"""
import os
import numpy as np
import pandas as pd
import traceback
from datetime import datetime
import tkinter as tk
from tkinter import filedialog
import torch

from configure import LABELS, POLARITY_MAP, ensure_output_dir, log_work, csv_ext
from text_SentimentAnalysis import analyze_text

def analyze_file(df, text_column, model, file_path=None, date_column=None, id_column=None, replace_none=False):
    """
    파일을 로드하고 감정 분석 수행
    
    Args:
        df (pd.DataFrame): 분석할 데이터프레임
        text_column (str): 텍스트 컬럼 이름
        model: 감정 분석 모델 인스턴스
        file_path (str, optional): 파일 경로
        date_column (str, optional): 날짜 컬럼 이름
        id_column (str, optional): ID 컬럼 이름
        replace_none (bool, optional): '없음'을 '무감정'으로 대체할지 여부
        
    Returns:
        tuple: (분석 결과 데이터프레임, 결과 텍스트, 원본 데이터프레임)
    """
    # 원본 데이터 복사 (참조 방지)
    original_df = df.copy()
    file_info = file_path if file_path else "데이터프레임 직접 입력"
    
    # 분석 시작 시간 기록
    analyze_start_time = datetime.now()
    
    # 분석 수행
    try:
        # 파일 메타데이터 저장
        metadata = {
            "파일정보": file_info,
            "전체행수": len(df),
            "분석컬럼": text_column
        }
        
        # 분석 시작 메시지
        result_text = f"파일 감정 분석 시작...\n\n"
        result_text += f"파일: {os.path.basename(file_info) if isinstance(file_info, str) else '데이터프레임'}\n"
        result_text += f"총 {len(df)}개 행 분석 중...\n\n"
        
        # 결과 데이터프레임 초기화
        results_df = df.copy()
        
        # 텍스트 컬럼 유효성 검사
        if text_column not in df.columns:
            error_msg = f"텍스트 컬럼 '{text_column}'이 데이터에 존재하지 않습니다."
            return None, error_msg, None
        
        # 결과 컬럼 추가
        results_df['주요_감정'] = None
        results_df['감정_강도'] = None
        results_df['감정_분류'] = None
        
        # 각 감정별 강도 컬럼 추가
        for emotion in LABELS:
            results_df[emotion] = 0.0
        
        # 감정 분류별 카운트
        emotion_counts = {}
        polarity_counts = {'긍정': 0, '부정': 0, '중립': 0}
        
        # CUDA 메모리 모니터링
        progress_interval = max(1, len(df) // 10)  # 10% 단위로 진행 상황 표시
        
        # 분석 시작 시간 (더 정확한 계산을 위해)
        start_time = datetime.now()
        
        # 각 행 분석
        for i, row in enumerate(df.itertuples()):
            # 텍스트 가져오기
            text = getattr(row, text_column, "")
            
            # 빈 텍스트는 건너뛰기
            if not text or (isinstance(text, str) and not text.strip()):
                continue
            
            try:
                # 모델 추론 - 입력 텍스트를 문자열로 변환하여 전달
                text_str = str(text).strip()
                with torch.no_grad():
                    output = model(text_str).cpu().numpy()[0]
                
                # 감정 분류 및 강도 계산
                top_emotion_idx = np.argmax(output)
                top_emotion = LABELS[top_emotion_idx]
                top_score = output[top_emotion_idx]
                top_polarity = POLARITY_MAP.get(top_emotion, '중립')
                
                # '없음'을 '무감정'으로 대체
                if replace_none and top_emotion == "없음":
                    top_emotion = "무감정"
                
                # 인덱스 찾기 (튜플 -> 인덱스)
                row_idx = row.Index
                
                # 감정 분석 결과 저장
                results_df.at[row_idx, '주요_감정'] = top_emotion
                results_df.at[row_idx, '감정_강도'] = float(top_score)
                results_df.at[row_idx, '감정_분류'] = top_polarity
                
                # 각 감정별 강도 저장
                for emotion_idx, emotion in enumerate(LABELS):
                    results_df.at[row_idx, emotion] = float(output[emotion_idx])
                
                # 감정 통계 업데이트
                emotion_counts[top_emotion] = emotion_counts.get(top_emotion, 0) + 1
                polarity_counts[top_polarity] = polarity_counts.get(top_polarity, 0) + 1
                
                # 진행 상황 표시
                if (i + 1) % progress_interval == 0 or i + 1 == len(df):
                    progress = (i + 1) / len(df) * 100
                    elapsed = (datetime.now() - start_time).total_seconds()
                    est_remaining = elapsed / (i + 1) * (len(df) - i - 1)
                    result_text += f"진행: {progress:.1f}% ({i+1}/{len(df)}) - 예상 남은 시간: {est_remaining:.1f}초\n"
            
            except Exception as e:
                print(f"행 {i}({row.Index}) 분석 중 오류: {str(e)}")
                # 오류 발생 시 빈 값으로 처리
                row_idx = row.Index
                results_df.at[row_idx, '주요_감정'] = '오류'
                results_df.at[row_idx, '감정_강도'] = 0.0
                results_df.at[row_idx, '감정_분류'] = '중립'
        
        # 소요 시간 계산
        elapsed_time = (datetime.now() - start_time).total_seconds()
        
        # 결과 요약
        result_text += f"\n분석 완료!\n"
        result_text += f"소요 시간: {elapsed_time:.2f}초 (평균 {elapsed_time/len(df):.4f}초/항목)\n\n"
        
        # 감정 분류별 통계
        result_text += "== 감정 분류별 통계 ==\n"
        for polarity, count in polarity_counts.items():
            percent = count / len(df) * 100 if len(df) > 0 else 0
            result_text += f"{polarity}: {count}개 ({percent:.1f}%)\n"
        
        # 상위 감정 통계
        result_text += "\n== 상위 감정 통계 (상위 5개) ==\n"
        sorted_emotions = sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)
        for emotion, count in sorted_emotions[:5]:
            percent = count / len(df) * 100 if len(df) > 0 else 0
            result_text += f"{emotion}: {count}개 ({percent:.1f}%)\n"
        
        # 감정 분석 결과 저장
        saved_path = save_file_analysis_results(results_df, file_info, replace_none)
        
        if saved_path:
            result_text += f"\n분석 결과가 저장되었습니다: {os.path.basename(saved_path)}\n"
        else:
            result_text += "\n결과 저장에 실패했습니다.\n"
        
        # 분석 결과에 메타데이터 추가
        results_df._metadata = {'analysis_file_path': saved_path}
        
        # 작업 기록 - 작업 종료 시간 및 추가 정보 기록
        analyze_end_time = datetime.now()
        소요시간 = (analyze_end_time - analyze_start_time).total_seconds()
        
        # 파일명 추출
        if isinstance(file_info, str):
            파일명 = os.path.basename(file_info)
        else:
            파일명 = "데이터프레임"
        
        # 작업 기록 저장
        log_work(
            "파일_감정분석", 
            analyze_start_time, 
            analyze_end_time, 
            분석건수=len(df), 
            파일명=파일명,
            기타정보=f"소요시간: {소요시간:.2f}초, 긍정: {polarity_counts['긍정']}개, 부정: {polarity_counts['부정']}개, 중립: {polarity_counts['중립']}개"
        )
        
        return results_df, result_text, original_df
        
    except Exception as e:
        error_msg = f"파일 분석 중 오류가 발생했습니다: {str(e)}"
        print(f"파일 분석 중 오류 발생: {e}")
        print(traceback.format_exc())
        
        # 작업 기록 - 오류 발생 시에도 기록
        analyze_end_time = datetime.now()
        log_work(
            "파일_감정분석_오류", 
            analyze_start_time, 
            analyze_end_time, 
            파일명=os.path.basename(file_info) if isinstance(file_info, str) else "데이터프레임",
            기타정보=f"오류: {str(e)}"
        )
        
        return None, error_msg, None

def save_file_analysis_results(results_df, original_file_path, replace_none=False):
    """
    파일 분석 결과를 저장
    
    Args:
        results_df: 분석 결과 데이터프레임
        original_file_path: 원본 파일 경로
        replace_none: '없음'을 '무감정'으로 대체할지 여부
        
    Returns:
        str: 저장된 파일 경로 또는 None
    """
    try:
        # output 디렉토리 확인 및 생성
        output_dir = ensure_output_dir()
        
        # 결과 저장 경로 설정 - 원본 파일명_타임스탬프 형식
        if isinstance(original_file_path, str) and os.path.exists(original_file_path):
            base_file_name = os.path.splitext(os.path.basename(original_file_path))[0]
        else:
            base_file_name = "분석결과"
            
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        result_file_name = f"{base_file_name}_감정분석결과_{timestamp}.csv"
        default_save_path = os.path.join(output_dir, result_file_name)
        
        # 결과 데이터프레임 복사 (원본 보존)
        save_df = results_df.copy()
        
        # 모든 감정 라벨이 포함되어 있는지 확인하고 추가
        all_emotions = set(LABELS)
        if replace_none:
            # '없음'을 '무감정'으로 대체하는 경우
            all_emotions.remove('없음')
            all_emotions.add('무감정')
        
        # 현재 감정 컬럼 목록
        existing_emotions = {col for col in save_df.columns if col in all_emotions or col == ('무감정' if replace_none else '없음')}
        
        # 누락된 감정 컬럼 식별
        missing_emotions = all_emotions - existing_emotions
        
        # 누락된 감정 컬럼 추가 (모두 0으로 초기화)
        for emotion in missing_emotions:
            save_df[emotion] = 0.0
            print(f"누락된 감정 컬럼 추가: {emotion}")
        
        # '없음'을 '무감정'으로 변경 처리
        if replace_none:
            # '없음' 컬럼이 있는 경우 처리
            if "없음" in save_df.columns:
                # '없음' 컬럼 값을 '무감정' 컬럼으로 복사
                if "무감정" not in save_df.columns:
                    save_df["무감정"] = save_df["없음"]
                else:
                    # 이미 '무감정' 컬럼이 있으면 기존 값과 '없음' 값 중 큰 값 사용
                    save_df["무감정"] = save_df[["무감정", "없음"]].max(axis=1)
                # '없음' 컬럼 삭제
                save_df = save_df.drop(columns=["없음"])
            
            # 주요 감정이 '없음'인 경우 '무감정'으로 변경
            save_df.loc[save_df['주요_감정'] == '없음', '주요_감정'] = '무감정'
        
        # 결과 저장 (직접 지정된 경로에 저장)
        save_df.to_csv(default_save_path, index=False, encoding='utf-8-sig')
        print(f"분석 결과가 저장되었습니다: {default_save_path}")
        print(f"저장된 감정 컬럼 수: {len(all_emotions)}, 컬럼 목록: {', '.join(sorted(save_df.columns))}")
        
        # 메타데이터에 파일 경로 추가
        save_df._metadata = {"analysis_file_path": default_save_path}
        
        return default_save_path
        
    except Exception as e:
        print(f"결과 저장 중 오류 발생: {str(e)}")
        print(traceback.format_exc())
        return None

def load_file(file_path=None):
    """
    파일을 로드하고 데이터프레임으로 반환
    
    Args:
        file_path (str, optional): 파일 경로, None이면 파일 선택 대화상자 표시
        
    Returns:
        tuple: (로드된 데이터프레임, 파일 정보 문자열)
    """
    # 파일 경로가 없으면 파일 선택 대화상자 표시
    if file_path is None:
        # 파일 선택 대화상자 표시
        file_path = filedialog.askopenfilename(
            title="파일 선택",
            filetypes=[
                ("데이터 파일", "*.csv;*.xlsx;*.xls;*.txt"),
                ("CSV 파일", "*.csv"),
                ("Excel 파일", "*.xlsx;*.xls"),
                ("텍스트 파일", "*.txt"),
                ("모든 파일", "*.*")
            ]
        )
    
    if not file_path:
        return None, "파일이 선택되지 않았습니다."
    
    try:
        # 파일 확장자 확인
        _, file_ext = os.path.splitext(file_path)
        file_ext = file_ext.lower()
        
        # 파일 로드
        if file_ext == '.csv':
            # CSV 파일
            try:
                df = pd.read_csv(file_path, encoding='utf-8-sig')
            except:
                df = pd.read_csv(file_path, encoding='cp949')
        elif file_ext in ['.xlsx', '.xls']:
            # Excel 파일
            df = pd.read_excel(file_path)
        elif file_ext == '.txt':
            # 텍스트 파일
            with open(file_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
            
            # 파일 정보 생성
            file_info = f"파일: {os.path.basename(file_path)}\n"
            file_info += f"크기: {len(text_content)} 문자\n"
            file_info += f"내용:\n{text_content[:300]}{'...' if len(text_content) > 300 else ''}"
            
            return None, text_content  # 텍스트 파일은 데이터프레임 대신 텍스트 반환
        else:
            return None, f"지원되지 않는 파일 형식입니다: {file_ext}"
        
        # 데이터프레임 메타데이터에 파일 경로 저장
        df._metadata = {"filepath": file_path}
        
        # 파일 정보 생성
        file_info = f"파일: {os.path.basename(file_path)}\n"
        file_info += f"행 수: {len(df)}\n"
        file_info += f"열 수: {len(df.columns)}\n"
        file_info += f"열 목록: {', '.join(df.columns.tolist())}\n"
        
        # 데이터 미리보기 추가
        preview_rows = min(5, len(df))
        if preview_rows > 0:
            file_info += f"\n처음 {preview_rows}행 미리보기:\n"
            preview_df = df.head(preview_rows)
            file_info += preview_df.to_string()
        
        # 작업 기록에 파일 로드 기록
        log_work(
            "파일_로드", 
            datetime.now(), 
            datetime.now(), 
            분석건수=len(df), 
            파일명=os.path.basename(file_path)
        )
        
        return df, file_info
        
    except Exception as e:
        error_msg = f"파일 로드 중 오류가 발생했습니다: {str(e)}"
        print(f"파일 로드 중 오류 발생: {e}")
        print(traceback.format_exc())
        return None, error_msg

def analyze_file_data(model, df, text_column, date_column=None, id_column=None, replace_none=False):
    """
    파일 데이터에 대한 감정 분석 수행
    
    Args:
        model: 감정 분석 모델 인스턴스
        df: 분석할 데이터프레임
        text_column: 텍스트 컬럼 이름
        date_column: 날짜 컬럼 이름 (선택사항)
        id_column: ID 컬럼 이름 (선택사항)
        replace_none: '없음'을 '무감정'으로 대체할지 여부
        
    Returns:
        tuple: (분석 결과 데이터프레임, 상세 결과 텍스트, 분석 결과가 추가된 원본 데이터프레임)
    """
    result_text = ""
    
    # 텍스트 컬럼 존재 확인
    if text_column not in df.columns:
        result_text = f"오류: 선택한 파일에 '{text_column}' 컬럼이 없습니다."
        return None, result_text, None
    
    # 데이터 확인
    if df.shape[0] == 0:
        result_text = "오류: 파일에 데이터가 없습니다."
        return None, result_text, None
    
    # 원본 데이터프레임 복사
    analyzed_df = df.copy()
    
    # 데이터 분석
    results = pd.DataFrame(index=range(len(df)))
    results['텍스트'] = df[text_column].fillna('')
    
    # 모든 감정 종류 리스트 생성
    all_emotions = LABELS.copy()
    
    # '없음'을 '무감정'으로 대체하는 경우
    if replace_none:
        all_emotions = [emotion if emotion != '없음' else '무감정' for emotion in all_emotions]
    
    # 빈 감정 목록 초기화 - 모든 감정 점수 컬럼을 0으로 초기화
    for label in all_emotions:
        results[label] = 0.0
    
    # 주요 감정 컬럼 추가
    results['주요_감정'] = ""
    results['감정_분류'] = ""
    results['감정_강도'] = 0.0
    
    # 빈 텍스트 카운터
    empty_text_count = 0
    error_count = 0
    
    # 각 행 분석
    for idx, row in df.iterrows():
        try:
            text = str(row[text_column]).strip()
            
            # 빈 텍스트 처리
            if not text:
                empty_text_count += 1
                
                # 빈 텍스트의 경우 '무감정' 또는 '없음'으로 설정
                emotion = "무감정" if replace_none else "없음"
                polarity = "중립"
                intensity = 0.0
                
                # 결과 저장
                results.at[idx, '주요_감정'] = emotion
                results.at[idx, '감정_분류'] = polarity
                results.at[idx, '감정_강도'] = intensity
                results.at[idx, emotion] = 1.0
                continue
            
            # 모델 추론 방식 확인 및 감정 추론
            try:
                # 예전 모델 호환성 확인: infer 메서드가 있는지 확인
                if hasattr(model, 'infer') and callable(getattr(model, 'infer')):
                    # infer 메서드 사용
                    emotions, intensity = model.infer(text)
                else:
                    # forward 메서드 사용 (기존 방식)
                    with torch.no_grad():
                        output = model(text).cpu().numpy()[0]
                    
                    # 감정 및 점수 맵핑
                    emotions = dict(zip(LABELS, output))
                    # 최대 감정 점수를 강도로 사용
                    intensity = max(output)
                
                # 최고 감정 식별
                if emotions:
                    # 모든 감정 점수 저장
                    for emotion, score in emotions.items():
                        # '없음'을 '무감정'으로 변경
                        emotion_key = '무감정' if emotion == '없음' and replace_none else emotion
                        results.at[idx, emotion_key] = score
                    
                    # 최대 감정 값과 키 찾기
                    max_emotion = max(emotions.items(), key=lambda x: x[1])
                    top_emotion = max_emotion[0]
                    top_score = max_emotion[1]
                    
                    # '없음'을 '무감정'으로 변경
                    if top_emotion == '없음' and replace_none:
                        top_emotion = '무감정'
                    
                    # 감정 분류 (극성) 결정
                    polarity = POLARITY_MAP.get(top_emotion, "중립")
                    
                    # 결과 저장
                    results.at[idx, '주요_감정'] = top_emotion
                    results.at[idx, '감정_분류'] = polarity
                    results.at[idx, '감정_강도'] = intensity
                else:
                    # 감정이 없는 경우 기본값 설정
                    emotion = "무감정" if replace_none else "없음"
                    results.at[idx, '주요_감정'] = emotion
                    results.at[idx, '감정_분류'] = "중립"
                    results.at[idx, '감정_강도'] = 0.0
                    results.at[idx, emotion] = 1.0
            
            except Exception as e:
                error_count += 1
                print(f"행 {idx} 분석 중 오류 발생: {str(e)}")
                traceback.print_exc()
                
                # 오류 시 기본값 설정
                emotion = "무감정" if replace_none else "없음"
                results.at[idx, '주요_감정'] = emotion
                results.at[idx, '감정_분류'] = "중립"
                results.at[idx, '감정_강도'] = 0.0
                results.at[idx, emotion] = 1.0
        
        except Exception as e:
            error_count += 1
            print(f"행 {idx} 분석 중 오류 발생: {str(e)}")
            traceback.print_exc()
            
            # 오류 시 기본값 설정
            emotion = "무감정" if replace_none else "없음"
            results.at[idx, '주요_감정'] = emotion
            results.at[idx, '감정_분류'] = "중립"
            results.at[idx, '감정_강도'] = 0.0
            results.at[idx, emotion] = 1.0
    
    # 기존 데이터프레임과 결과 합치기
    results.index = df.index  # 인덱스 맞추기
    
    # 원본 데이터와 결과 데이터 병합
    merged_results = pd.concat([df, results.drop(columns=['텍스트'])], axis=1)
    
    # 결과 저장
    save_path = save_file_analysis_results(merged_results, text_column, replace_none)
    
    # 상세 결과 텍스트 생성
    result_text += f"\n\n전체 {len(df)}개 항목의 분석 결과가 저장되었습니다."
    
    if save_path:
        result_text += f"\n저장 경로: {save_path}"
        result_text += f"\n저장된 결과에는 원본 데이터와 모든 감정 유형({len(LABELS)}개)의 점수가 포함되어 있습니다."
        # '없음' 대체 정보 추가
        if replace_none:
            result_text += f"\n'없음'은 '무감정'으로 대체되었습니다."
    else:
        result_text += "\n결과 저장에 실패했습니다."
    
    return merged_results, result_text, analyzed_df

if __name__ == "__main__":
    # 테스트용 코드
    from KOTE_load import load_model
    
    device = torch.device("cpu")
    model = load_model(device)
    
    # 파일 로드 테스트
    print("\n파일 로드 테스트를 시작합니다...")
    data, preview = load_file()
    if data is not None:
        print(preview)
        
        if isinstance(data, pd.DataFrame):
            # 첫 번째 열에 대해 분석 테스트
            results_df, result_text, save_path = analyze_file(data, data.columns[0], model)
            print(result_text) 