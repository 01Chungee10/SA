"""
감정 분석 애플리케이션 실행 모듈
"""
import sys
import traceback
import urllib3
import warnings

# 먼저 SSL 관련 경고 억제
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

# SSL 패치 적용 (기본적인 SSL 검증 비활성화)
try:
    from ssl_patch import init_ssl_patch
    init_ssl_patch()
except ImportError:
    print("SSL 패치 모듈을 찾을 수 없습니다. SSL 인증서 경고가 발생할 수 있습니다.")
except Exception as e:
    print(f"SSL 패치 적용 중 오류: {str(e)}")

from app import EmotionAnalysisApp
from configure import resource_path, init_config

def main():
    """메인 애플리케이션 실행 함수"""
    try:
        # 기본 설정 초기화
        init_config()
        
        # 애플리케이션 시작
        app = EmotionAnalysisApp()
        app.load_model_and_start()
    except Exception as e:
        print(f"프로그램 실행 중 오류 발생: {str(e)}")
        traceback.print_exc()
        sys.exit(1)

# 애플리케이션 실행
if __name__ == "__main__":
    main() 