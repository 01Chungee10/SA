# 만든 이가 올리는 말
안녕하세요. 성장디자인팀 한충석 책임매니저입니다.
업무를 수행하면서 얻게되는 수많은 데이터 중에서
'주관식'으로 쓰여진 텍스트를 쓴 '사람'의 '마음'은 어떤지 궁금하지 않으셨나요?
이제 텍스트 행간에 숨겨진 글쓴이의 감정을 읽어보세요.

# 감정 분석 프로그램
이 프로그램은 텍스트의 감정을 분석하고 결과를 시각화하는 GUI 애플리케이션입니다.
직접 입력한 텍스트에 대해서 즉시 감정을 분석할 수 있고,
csv 파일의 특정 열에 존재하는 텍스트의 모든 행에 대해서 일괄분석도 가능합니다.
파일분석을 통해 추출한 감정분석의 결과는
마치 Excel에서 피벗테이블을 생성하듯이 빈도와 비율분석 결과도 만들 수 있습니다.
https://github.com/searle-j/KOTE 에서 제공되는 데이터 셋을 이용했습니다.

## 모듈 구조
프로젝트는 다음과 같은 모듈로 구성되어 있습니다:

### 핵심 GUI 모듈
- `gui_main.py`: 애플리케이션 진입점 (기본 실행 스크립트)
- `run.py`: SSL 패치 및 환경 설정을 포함한 확장 실행 스크립트
- `app.py`: 메인 애플리케이션 프레임워크 클래스 (`EmotionAnalysisApp`)
- `emotion_analysis_gui.py`: 감정 분석 GUI 컴포넌트 (`EmotionAnalysisGUI`)
- `gui_utils.py`: GUI 유틸리티 함수와 클래스
- `statistics_gui.py`: 통계 분석 GUI 모듈 (`StatisticsGUI`)
- `GUI.py`: 이전 버전과의 호환성을 위한 레거시 파일

### 감정 분석 기능 모듈
- `KOTE_load.py`: 감정 분석 모델 로드 및 초기화
- `text_SentimentAnalysis.py`: 텍스트 감정 분석 기능
- `file_SentimentAnalysis.py`: 파일 기반 감정 분석 기능

### 유틸리티 모듈
- `configure.py`: 설정 및 상수 정의
- `ssl_patch.py`: SSL 관련 패치

## 실행 방법

프로그램은 다음과 같이 실행할 수 있습니다:

```bash
# 필요 패키지 설치
pip install -r requirements.txt

# 기본 실행 방법
python gui_main.py

# 또는 SSL 패치 및 추가 초기화를 포함한 실행 방법
python run.py
```

## 파일 구조

```
감정분석/
├── gui_main.py          # 애플리케이션 진입점 (기본)
├── run.py               # 애플리케이션 진입점 (확장)
├── app.py               # 메인 애플리케이션 클래스
├── emotion_analysis_gui.py # 감정 분석 GUI 컴포넌트
├── gui_utils.py         # GUI 유틸리티 함수
├── statistics_gui.py    # 통계 분석 모듈
├── file_SentimentAnalysis.py # 파일 감정 분석 기능
├── text_SentimentAnalysis.py # 텍스트 감정 분석 기능
├── KOTE_load.py         # 모델 로딩 모듈
├── configure.py         # 설정 모듈
├── ssl_patch.py         # SSL 패치 모듈
├── GUI.py               # 레거시 모듈
├── requirements.txt     # 필요 패키지 목록
├── kote_pytorch_lightning.bin # 감정 분석 모델 파일
├── model_cache/         # 모델 캐시 디렉토리 
└── output/              # 분석 결과 출력 디렉토리
```

## 주요 기능

1. **텍스트 감정 분석**: 직접 입력한 텍스트에 대한 감정 분석 수행
2. **파일 감정 분석**: CSV, Excel 파일의 특정 열에 대한 감정 분석 수행
3. **통계 분석**: 감정 분석 결과에 대한 다양한 통계 분석 및 그룹핑 기능
4. **결과 저장**: 분석 결과를 Excel 파일로 저장 