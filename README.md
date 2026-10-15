# KDT-CLASS

KDT 교육 과정에서 학습한 Python, 웹 백엔드, 머신러닝, 딥러닝, LLM 및 RAG 실습 코드를 정리한 저장소입니다.

이 저장소는 학습 과정과 구현 코드를 기록하는 것이 목적입니다. 용량이 큰 원본 데이터셋, 학습된 모델, 체크포인트, 가상환경 및 실행 중 생성되는 파일은 저장소에 포함하지 않습니다.

## Curriculum

| 순서 | 폴더 | 주요 내용 |
| --- | --- | --- |
| 01 | [`01_python-basic`](./01_python-basic/) | Python 기본 문법, 자료구조, 함수, 클래스, 예외 처리, 정규표현식, NumPy, pandas, 데이터 시각화 및 데이터 분석 실습 |
| 02 | [`02_job-scrapper`](./02_job-scrapper/) | Requests와 BeautifulSoup을 이용한 웹 스크래핑, Flask 검색 화면, CSV 내보내기 |
| 03 | [`03_apt-api`](./03_apt-api/) | 공공데이터포털 아파트 실거래 API 호출, XML 파싱, Flask 기반 조회 화면 |
| 04 | [`04_todos`](./04_todos/) | Todo 서비스를 단계별로 확장하며 템플릿, 데이터베이스, 로그인, 프론트엔드 연동, 외래키 및 MVC 구조 학습 |
| 05 | [`05_fast-api`](./05_fast-api/) | FastAPI 라우팅, 타입 힌트, HTTP 메서드, Pydantic 검증, 응답 모델, 예외 처리, 템플릿 및 데이터베이스 |
| 06 | [`06_aws-docker`](./06_aws-docker/) | Docker Compose를 이용한 백엔드·Nginx 구성과 배포 환경 실습 |
| 07 | [`07_Machine_Learning`](./07_Machine_Learning/) | 전처리, 분류, 회귀, 앙상블, 차원 축소, 군집화 및 모델 평가를 포함한 전통적 머신러닝 |
| 08 | [`08_image_bible`](./08_image_bible/) | TensorFlow/Keras 기반 CNN, 오토인코더, 전이학습, 객체 탐지 및 이미지 분할 |
| 09 | [`09_PyTorch`](./09_PyTorch/) | PyTorch 텐서와 자동 미분, 신경망, CNN, 전이학습, 시계열 및 이미지 분할 실습 |
| 10 | [`10_LLM_CV`](./10_LLM_CV/) | 한국어 말뭉치, 토크나이저, 임베딩, RNN/Transformer 및 사전학습 언어 모델 활용 |
| 11 | [`11_bot`](./11_bot/) | Attention과 GPT 구현, CodeBot·StoryBot·WebBot 학습 코드, FastAPI·React 웹서비스 |
| 12 | [`12_VT`](./12_VT/) | Fashion-MNIST를 이용한 Vision Transformer, Swin Transformer 및 CvT 실습 |
| 13 | [`13_rag`](./13_rag/) | 임베딩, ChromaDB, Ollama, 감정 분석, 이미지 생성 및 LoRA를 결합한 RAG 기반 AI 비서 |

## Repository policy

다음 항목은 GitHub 저장소에서 제외합니다.

- 원본 이미지, CSV, 압축 파일 등 실습용 대용량 데이터셋
- `.pt`, `.pth`, `.h5`, `.safetensors` 등의 학습 모델과 체크포인트
- ChromaDB 인덱스, SQLite 데이터베이스, 생성 이미지 및 로그
- Python 가상환경, 패키지 캐시, Jupyter 체크포인트 및 IDE 설정
- API 키와 서비스 키가 저장되는 `.env` 파일
- 설치 프로그램과 외부 프로젝트를 그대로 복사한 소스 트리

노트북과 소스 코드에서 데이터를 자동으로 내려받는 경우에는 해당 셀을 실행하면 됩니다. 로컬 파일 경로를 사용하는 실습은 아래 출처에서 데이터를 내려받은 뒤, 노트북에 적힌 경로에 배치해야 합니다.

## Getting started

저장소를 복제한 뒤 실습하려는 폴더로 이동하여 별도 가상환경을 만드는 것을 권장합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

폴더에 `requirements-windows.txt`, `requirement.txt`처럼 별도 의존성 파일이 있는 경우 해당 파일을 사용합니다. 일부 과정은 Python 또는 CUDA 버전이 다르므로 각 노트북의 첫 번째 설정 셀과 폴더 내부 문서를 먼저 확인해야 합니다.

공공 API와 외부 서비스의 인증정보는 소스에 직접 입력하지 않고 환경변수로 전달합니다.

```env
SERVICE_KEY=공공데이터포털_서비스키
OPENAI_API_KEY=OpenAI_API_키
```

`13_rag`의 로컬 LLM 예제는 기본적으로 Ollama의 `gemma3:4b` 모델과 `http://localhost:11434`를 사용합니다. 모델과 생성된 인덱스는 저장소에 포함되지 않습니다.

## Dataset sources

아래는 노트북과 코드에서 확인한 대표 데이터 출처입니다. 저장소에 포함되지 않은 데이터의 저작권과 라이선스는 각 제공처의 정책을 따릅니다.

| 사용 과정 | 데이터 또는 서비스 | 출처 |
| --- | --- | --- |
| 01 데이터 분석 | 공기질, 직원 이탈, 생활 데이터 등 유형별 연습 자료 | [`YoungjinBD/dataset`](https://github.com/YoungjinBD/dataset) |
| 01 데이터 분석 | Titanic 등 Seaborn 예제 데이터 | [`mwaskom/seaborn-data`](https://github.com/mwaskom/seaborn-data) |
| 02 웹 스크래핑 | 채용 및 도서 검색 결과 | [인크루트](https://www.incruit.com/), [알라딘](https://www.aladin.co.kr/) 공개 검색 페이지 |
| 03 공공 API | 국토교통부 아파트 매매 실거래 자료 | [공공데이터포털 API 상세 페이지](https://www.data.go.kr/data/15126469/openapi.do) |
| 07 머신러닝 | Iris, Digits, Breast Cancer 등 내장 데이터 | [scikit-learn datasets](https://scikit-learn.org/stable/datasets.html) |
| 07 머신러닝 | Titanic 생존자 예측 | [Kaggle Titanic](https://www.kaggle.com/competitions/titanic/data) |
| 08 이미지 처리 | MNIST, CIFAR-10, CIFAR-100 | [TensorFlow/Keras datasets](https://www.tensorflow.org/api_docs/python/tf/keras/datasets), [CIFAR 원본](https://cave.cs.toronto.edu/kriz/cifar.html) |
| 08 이미지 처리 | 객체 탐지용 PASCAL VOC 2007 | [The PASCAL Visual Object Classes Challenge](https://www.robots.ox.ac.uk/~vgg/projects/pascal/VOC/voc2007/) |
| 09 PyTorch | MNIST, CIFAR-10 | [TorchVision datasets](https://docs.pytorch.org/vision/stable/datasets.html) |
| 09 PyTorch | Cityscapes 이미지 분할 | [Cityscapes Dataset](https://www.cityscapes-dataset.com/) |
| 10 LLM/CV | Korean Petitions, NSMC, KorNLI | [Korpora](https://github.com/ko-nlp/Korpora) |
| 10 LLM/CV | 뉴스 요약 데이터 | [Hugging Face `argilla/news-summary`](https://huggingface.co/datasets/argilla/news-summary) |
| 11 Bot | TinyCodes, TinyStories 및 OpenWebText 계열 학습 텍스트 | 수업 실습용 로컬 자료로 사용하며 원본 데이터는 저장소에서 제외 |
| 12 Vision Transformer | Fashion-MNIST | [`zalandoresearch/fashion-mnist`](https://github.com/zalandoresearch/fashion-mnist) |
| 13 RAG | NSMC 감정 분석 데이터 | [`e9t/nsmc`](https://github.com/e9t/nsmc) |
| 13 RAG | 동아리 소개·과정·장비·행사·FAQ 지식 문서 | 이 저장소의 [`13_rag/data/knowledge`](./13_rag/data/knowledge/)에 포함된 실습용 문서 |

## Notes

- 노트북은 수업 당시의 실행 결과를 일부 포함할 수 있습니다.
- 라이브러리 버전 차이로 경고 또는 API 변경이 발생할 수 있으므로 폴더별 의존성 파일을 우선 사용하세요.
- 모델 파일이 필요한 예제는 노트북을 처음부터 실행해 직접 학습하거나, 노트북에 안내된 모델을 별도로 준비해야 합니다.
- 외부 웹사이트와 API를 사용하는 코드는 각 서비스의 이용약관, 호출 제한 및 robots 정책을 확인한 뒤 실행하세요.
