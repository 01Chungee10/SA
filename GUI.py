"""
감정 분석 GUI 모듈 (레거시 파일) - 이전 버전 호환성 유지
"""
import sys
import traceback

def main():
    """레거시 호환성을 위한 메인 함수"""
    try:
        # 최신 코드로 리디렉션
        from gui_main import main as new_main
        print("감정분석 프로그램을 시작합니다...")
        print("참고: 이제 gui_main.py 또는 run.py를 사용하는 것을 권장합니다.")
        new_main()
    except Exception as e:
        print(f"프로그램 실행 중 오류 발생: {str(e)}")
        traceback.print_exc()
        sys.exit(1)

# 애플리케이션 실행 (이전 코드와 호환성 유지)
if __name__ == "__main__":
    main() 