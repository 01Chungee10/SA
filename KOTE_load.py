"""
KOTE 감정 분석 모델 로딩 모듈
"""
import os
import torch
import traceback
import torch.nn as nn
import pytorch_lightning as pl
from transformers import ElectraModel, AutoTokenizer
import tkinter as tk
from tkinter import messagebox

from ssl_patch import no_ssl_verification_requests, no_ssl_verification_httpx
from configure import resource_path, ensure_output_dir, log_work, LABELS

class KOTEtagger(pl.LightningModule):
    """KOTE 감정 분석 모델 클래스"""
    def __init__(self, offline_mode=False, device=None):
        super().__init__()
        
        # device를 클래스 변수로 설정하는 대신 별도의 인스턴스 변수로 관리
        self._device = device if device is not None else torch.device("cpu")
        
        # SSL 검증 비활성화 컨텍스트 내에서 모델 로드
        with no_ssl_verification_requests(), no_ssl_verification_httpx():
            # 오프라인 모드일 경우 로컬 모델 파일 사용
            if offline_mode:
                try:
                    # 먼저 실행 파일과 동일한 위치에 모델 폴더가 있는지 확인
                    model_dir = os.path.dirname(os.path.abspath(__file__))
                    config_path = os.path.join(model_dir, 'model_files', 'electra_config')
                    tokenizer_path = os.path.join(model_dir, 'model_files', 'electra_tokenizer')
                    
                    # 폴더 존재 여부 확인
                    if os.path.exists(config_path) and os.path.exists(tokenizer_path):
                        print(f"로컬 모델 폴더 경로: {config_path}")
                        self.electra = ElectraModel.from_pretrained(config_path)
                        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
                    else:
                        # 폴더가 없으면 온라인 모드로 전환
                        print("로컬 모델 폴더를 찾을 수 없습니다. 온라인 모드로 전환합니다.")
                        raise FileNotFoundError("모델 폴더가 존재하지 않습니다")
                except Exception as e:
                    print(f"로컬 모델 로드 실패: {e}")
                    # 온라인 로드 시도
                    print("온라인 모드로 전환하여 모델을 로드합니다...")
                    self.electra = ElectraModel.from_pretrained("beomi/KcELECTRA-base", revision='v2021')
                    self.tokenizer = AutoTokenizer.from_pretrained("beomi/KcELECTRA-base", revision='v2021')
            else:
                # 온라인 모드 - HuggingFace에서 다운로드
                try:
                    self.electra = ElectraModel.from_pretrained("beomi/KcELECTRA-base", revision='v2021')
                    self.tokenizer = AutoTokenizer.from_pretrained("beomi/KcELECTRA-base", revision='v2021')
                except Exception as e:
                    print(f"온라인 모델 로드 실패: {e}")
                    messagebox.showerror("모델 로드 오류", f"ELECTRA 모델을 로드하는데 실패했습니다.\n{str(e)}")
                    exit(1)
                
        self.classifier = nn.Linear(self.electra.config.hidden_size, 44)
        self.to(self._device)

    def forward(self, text):
        """텍스트에 대한 감정 분석 수행"""
        try:
            # 입력 텍스트 검증 및 처리
            if text is None:
                text = ""
            
            # 입력이 문자열이 아닌 경우 문자열로 변환
            if not isinstance(text, str):
                text = str(text)
            
            # 빈 문자열 처리
            if not text.strip():
                return torch.zeros((1, 44), device=self._device)
            
            encoding = self.tokenizer.encode_plus(
                text,
                add_special_tokens=True,
                max_length=512,
                return_token_type_ids=False,
                padding="max_length",
                return_attention_mask=True,
                return_tensors='pt',
                truncation=True
            ).to(self._device)
            output = self.electra(encoding["input_ids"], attention_mask=encoding["attention_mask"])
            output = output.last_hidden_state[:, 0, :]
            output = self.classifier(output)
            output = torch.sigmoid(output)
            return output
        except Exception as e:
            print(f"추론 중 오류 발생: {e}")
            print(traceback.format_exc())
            # 오류 발생 시 0으로 채워진 텐서 반환
            return torch.zeros((1, 44), device=self._device)

    # device에 대한 getter 메서드 추가
    def get_device(self):
        return self._device
    
    def infer(self, text):
        """텍스트에 대한 감정 분석을 수행하고 감정-점수 사전과 강도를 반환
        
        Args:
            text (str): 분석할 텍스트
            
        Returns:
            tuple: (감정-점수 사전, 최대 감정 강도)
        """
        try:
            # 입력 텍스트 검증 및 처리
            if text is None or not isinstance(text, str) or not text.strip():
                # 빈 텍스트인 경우 빈 결과 반환
                return {}, 0.0
            
            # forward 메서드 사용하여 추론 실행
            with torch.no_grad():
                output = self(text).cpu().numpy()[0]
            
            # 감정 점수 추출 및 사전 생성
            emotions_dict = dict(zip(LABELS, output))
            
            # 최대 감정 강도 계산
            max_intensity = max(output)
            
            return emotions_dict, float(max_intensity)
            
        except Exception as e:
            print(f"감정 추론 중 오류 발생: {str(e)}")
            print(traceback.format_exc())
            return {}, 0.0

def load_model(device=None):
    """감정 분석 모델 로드 함수"""
    import time
    start_time = time.time()
    
    print("감정분석 모델을 불러오는 중입니다...")
    
    # 모델 인스턴스 생성
    trained_model = KOTEtagger(offline_mode=True, device=device)
    
    # 모델 파일명 설정 (상대 경로)
    model_file = "kote_pytorch_lightning.bin"
    model_path = resource_path(model_file)
    
    # 경로 및 파일 존재 여부 확인
    print(f"모델 파일 경로: {model_path}")
    
    # 모델 디렉토리가 없으면 생성
    model_dir = os.path.dirname(model_path)
    if model_dir and not os.path.exists(model_dir):
        os.makedirs(model_dir, exist_ok=True)
    
    if os.path.isfile(model_path):
        print("모델 파일이 존재합니다.")
        # PyTorch 버전 확인
        print(f"PyTorch 버전: {torch.__version__}")
        try:
            # 모델 로딩 시도
            try:
                # PyTorch 2.1.0 이상인 경우 weights_only=True 사용 시도
                # 오류 발생 시 다양한 옵션으로 재시도
                try:
                    if torch.__version__ >= '2.1.0':
                        state_dict = torch.load(model_path, weights_only=True, map_location=device)
                    else:
                        # PyTorch 2.1.0 미만인 경우 weights_only 인자 사용 불가
                        state_dict = torch.load(model_path, map_location=device)
                except (TypeError, AttributeError) as e:
                    print(f"TypeError/AttributeError 발생: {e}. 다른 옵션으로 시도합니다.")
                    state_dict = torch.load(model_path, map_location=device)
                
                trained_model.load_state_dict(state_dict, strict=False)
                print("<All keys matched successfully>")
            except Exception as e:
                print(f"모델 로딩 중 예외 발생: {e}")
                print(traceback.format_exc())
                
                # 예외 발생시 대화상자 표시
                root = tk.Tk()
                root.withdraw()  # 빈 창 숨기기
                messagebox.showerror("모델 로딩 오류", 
                                   f"모델 파일 '{model_path}'을 로딩하는 중 오류가 발생했습니다.\n\n"
                                   f"오류 내용: {str(e)}\n\n"
                                   f"프로그램을 종료합니다.")
                root.destroy()
                exit(1)  # 치명적 오류로 프로그램 종료
        except Exception as e:
            print(f"예상치 못한 오류 발생: {e}")
            print(traceback.format_exc())
            exit(1)
    else:
        print(f"모델 파일을 찾을 수 없습니다: {model_path}")
        
        # 모델 파일 없을 시 대화상자 표시 및 종료
        root = tk.Tk()
        root.withdraw()  # 빈 창 숨기기
        messagebox.showerror("모델 파일 오류", 
                            f"모델 파일 '{model_path}'을 찾을 수 없습니다.\n\n"
                            f"올바른 경로에 모델 파일이 있는지 확인하세요.\n\n"
                            f"프로그램을 종료합니다.")
        root.destroy()
        exit(1)  # 치명적 오류로 프로그램 종료
    
    # 작업 완료 시간과 소요 시간 계산
    end_time = time.time()
    elapsed_time = round(end_time - start_time, 2)
    
    # 작업 완료 메시지 출력
    print(f"감정분석에 필요한 모델이 모두 로딩되었습니다.\n소요된 시간은 {elapsed_time}초 입니다.")
    
    # 작업 기록 저장
    log_work("감정분석 모델로딩", start_time, end_time)
    
    return trained_model

def load_custom_model(model_path, device=None):
    """
    사용자가 선택한 모델 파일을 로드하는 함수
    
    Args:
        model_path: 모델 파일 경로
        device: 장치 (CPU/GPU)
        
    Returns:
        trained_model: 학습된 모델 인스턴스
    """
    import time
    start_time = time.time()
    
    print(f"사용자 지정 모델을 불러오는 중입니다: {model_path}")
    
    # 모델 인스턴스 생성
    trained_model = KOTEtagger(offline_mode=False, device=device)
    
    # 경로 및 파일 존재 여부 확인
    if not os.path.isfile(model_path):
        raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {model_path}")
    
    print("모델 파일이 존재합니다.")
    # PyTorch 버전 확인
    print(f"PyTorch 버전: {torch.__version__}")
    
    # 모델 로딩 시도
    try:
        # PyTorch 2.1.0 이상인 경우 weights_only=True 사용 시도
        try:
            if torch.__version__ >= '2.1.0':
                state_dict = torch.load(model_path, weights_only=True, map_location=device)
            else:
                # PyTorch 2.1.0 미만인 경우 weights_only 인자 사용 불가
                state_dict = torch.load(model_path, map_location=device)
        except (TypeError, AttributeError) as e:
            print(f"TypeError/AttributeError 발생: {e}. 다른 옵션으로 시도합니다.")
            state_dict = torch.load(model_path, map_location=device)
        
        trained_model.load_state_dict(state_dict, strict=False)
        print("<All keys matched successfully>")
    except Exception as e:
        print(f"모델 로딩 중 예외 발생: {e}")
        print(traceback.format_exc())
        raise Exception(f"모델 로딩 실패: {str(e)}")
    
    # 작업 완료 시간과 소요 시간 계산
    end_time = time.time()
    elapsed_time = round(end_time - start_time, 2)
    
    # 작업 완료 메시지 출력
    print(f"감정분석에 필요한 모델이 모두 로딩되었습니다.\n소요된 시간은 {elapsed_time}초 입니다.")
    
    # 작업 기록 저장
    log_work("사용자지정 감정분석 모델로딩", start_time, end_time)
    
    return trained_model

if __name__ == "__main__":
    # 테스트 코드
    device = torch.device("cpu")
    model = load_model(device)
    
    # 샘플 텍스트로 테스트
    test_text = "오늘은 정말 행복한 하루였어요!"
    preds = model(test_text)[0].cpu().detach().numpy()
    
    # 상위 5개 감정 출력
    emotion_scores = [(LABELS[i], score) for i, score in enumerate(preds)]
    emotion_scores.sort(key=lambda x: x[1], reverse=True)
    
    print("\n테스트 감정 분석 결과:")
    for emotion, score in emotion_scores[:5]:
        print(f"{emotion}: {score:.4f}") 