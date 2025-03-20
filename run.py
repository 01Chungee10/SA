"""
감정 분석 프로그램 실행 파일 - 추가 초기화 기능 포함
"""
import time
import sys
import os
import warnings

# 미리 모든 DeprecationWarning 억제
warnings.filterwarnings("ignore", category=DeprecationWarning)

# 표준 에러 출력 리다이렉션 (경고 메시지 숨김용)
class NullWriter:
    def write(self, string):
        pass
    def flush(self):
        pass

# 원래 에러 출력 저장
original_stderr = sys.stderr
# 처음에 표준 에러 리다이렉션 (urllib3 관련 경고 숨김)
sys.stderr = NullWriter()

def restore_stderr():
    """표준 에러 출력 복원"""
    global original_stderr
    sys.stderr = original_stderr

def main():
    """메인 실행 함수"""
    # 시작 시간 기록
    start_time = time.time()
    
    print("현대제철인의 감정을 읽는다 - 감정 분석 프로그램을 시작합니다...")
    
    app = None
    
    try:
        # 먼저 SSL 경고를 미리 비활성화
        import urllib3
        # 모든 SSL 관련 경고 비활성화
        urllib3.disable_warnings()
        warnings.filterwarnings('ignore', message='Unverified HTTPS request')
        warnings.filterwarnings('ignore', category=urllib3.exceptions.InsecureRequestWarning)
        warnings.filterwarnings('ignore', message='.*urllib3\[secure\].*')
        
        # 표준 에러 출력 복원
        restore_stderr()
        
        # SSL 패치 적용
        from ssl_patch import init_ssl_patch, patch_ssl_modules
        print("SSL 패치 적용 중...")
        init_ssl_patch()
        patch_ssl_modules()
        
        # 기본 설정 초기화
        from configure import init_config
        print("기본 설정 초기화 중...")
        init_config()
        
        # GUI 애플리케이션 생성 및 시작
        from app import EmotionAnalysisApp
        print("감정 분석 애플리케이션 시작 중...")
        
        # 애플리케이션 인스턴스 생성 및 실행
        app = EmotionAnalysisApp()
        app.load_model_and_start()
        
    except ImportError as e:
        # 표준 에러 출력 복원
        restore_stderr()
        
        print(f"모듈 가져오기 오류: {e}")
        print("필요한 모듈이 설치되어 있는지 확인하세요.")
        input("엔터 키를 눌러 종료하세요...")
        sys.exit(1)
    except Exception as e:
        # 표준 에러 출력 복원
        restore_stderr()
        
        print(f"프로그램 실행 중 오류가 발생했습니다: {e}")
        import traceback
        traceback.print_exc()
        input("엔터 키를 눌러 종료하세요...")
        sys.exit(1)
    finally:
        # 종료 정리 작업
        # 표준 출력 및 에러 스트림 복원
        restore_stderr()
        
        if app is not None and hasattr(app, 'restore_stdout'):
            try:
                app.restore_stdout()
            except:
                pass
    
    # 종료 시간 기록
    end_time = time.time()
    total_time = end_time - start_time
    
    # 안전하게 종료 메시지 출력 (일반 print 사용)
    original_stdout = sys.__stdout__
    original_stdout.write(f"프로그램 종료: 총 실행 시간 {total_time:.2f}초\n")

if __name__ == "__main__":
    main() 