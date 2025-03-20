"""
SSL 인증 검증 비활성화 환경 설정 모듈
"""
import os
import ssl
import urllib3
import warnings
import sys
import inspect
import requests
import httpx
from urllib3.connectionpool import HTTPSConnectionPool
from requests.adapters import HTTPAdapter

def init_ssl_patch():
    """SSL 인증 검증 비활성화 초기 설정을 수행"""
    # 경고 메시지 억제 (강화)
    warnings.filterwarnings('ignore', message='Unverified HTTPS request')
    warnings.filterwarnings('ignore', category=urllib3.exceptions.InsecureRequestWarning)
    warnings.filterwarnings('ignore', category=DeprecationWarning)
    warnings.filterwarnings('ignore', message='.*urllib3\[secure\].*')
    
    # 더 강력한 경고 억제 설정 추가
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # requests에서의 경고 억제
    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

    # SSL 검증 비활성화 (실행 시점에서 적용)
    ssl._create_default_https_context = ssl._create_unverified_context
    
    # 환경 변수 설정
    os.environ['CURL_CA_BUNDLE'] = ''
    os.environ['REQUESTS_CA_BUNDLE'] = ''
    os.environ['SSL_CERT_FILE'] = ''
    
    # Hugging Face 라이브러리용 환경 변수 설정
    os.environ['HF_HUB_DISABLE_SSL_VERIFICATION'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '0'
    os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'
    os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
    os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
    os.environ['PYTHONWARNINGS'] = 'ignore::DeprecationWarning'

    print("[SSL 패치] SSL 인증 검증 비활성화 환경 설정 완료")

def patch_ssl_modules():
    """SSL 인증 관련 패키지들을 직접 패치하여 SSL 검증을 비활성화합니다."""
    print("[SSL 패치] SSL 인증 관련 패키지 패치 중...")
    
    patch_functions = [
        # (패치 함수, 성공 메시지, 실패 시 무시 여부)
        (patch_urllib3, "urllib3 연결 검증 패치 완료", False),
        (patch_requests, "requests HTTPAdapter/세션 패치 완료", False),
        (patch_httpx, "httpx 패치 완료", True),
        (patch_huggingface, "huggingface_hub 패치 완료", True),
        (patch_transformers, "transformers 패치 완료", True),
        (patch_global_ssl, "글로벌 SSL 검증 패치 완료", False)
    ]
    
    for patch_func, success_msg, optional in patch_functions:
        try:
            patch_func()
            print(f"[SSL 패치] {success_msg}")
        except ImportError:
            if not optional:
                print(f"[SSL 패치] 필수 모듈을 찾을 수 없습니다.")
            # 선택적 모듈은 메시지 출력 생략
        except Exception as e:
            print(f"[SSL 패치] 패치 실패: {e}")
    
    print("[SSL 패치] SSL 인증 관련 패키지 패치 완료")

def patch_global_ssl():
    """전역적인 SSL 설정 패치"""
    # monkeypatch 방식으로 글로벌 SSL 컨텍스트 변경
    original_ssl_context = ssl.create_default_context
    
    def patched_create_context(*args, **kwargs):
        context = original_ssl_context(*args, **kwargs)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context
    
    ssl.create_default_context = patched_create_context

def patch_urllib3():
    """urllib3 패치"""
    # 모든 경고 억제
    urllib3.disable_warnings()
    
    # 원본 검증 함수 백업
    original_validate_conn = HTTPSConnectionPool._validate_conn
    
    def patched_validate_conn(self, conn):
        # SSL 연결 설정 완전 비활성화
        conn.cert_reqs = ssl.CERT_NONE
        conn.ca_certs = None
        if hasattr(conn, 'assert_hostname'):
            conn.assert_hostname = False
        if hasattr(conn, 'assert_fingerprint'):
            conn.assert_fingerprint = None
        return original_validate_conn(self, conn)
    
    HTTPSConnectionPool._validate_conn = patched_validate_conn
    
    # HTTPSConnectionPool에 추가 패치 적용
    original_init = HTTPSConnectionPool.__init__
    
    def patched_https_init(self, *args, **kwargs):
        kwargs['cert_reqs'] = 'CERT_NONE'
        kwargs['assert_hostname'] = False
        return original_init(self, *args, **kwargs)
    
    HTTPSConnectionPool.__init__ = patched_https_init

def patch_requests():
    """requests 패치"""
    # HTTPAdapter 패치
    original_init = HTTPAdapter.__init__
    def patched_init(self, *args, **kwargs):
        kwargs.update({
            'pool_connections': kwargs.get('pool_connections', 10),
            'pool_maxsize': kwargs.get('pool_maxsize', 10),
            'pool_block': kwargs.get('pool_block', False)
        })
        original_init(self, *args, **kwargs)
        if not hasattr(self, 'config'):
            self.config = {}
        self.config['verify'] = False
    
    HTTPAdapter.__init__ = patched_init
    
    # Session 패치
    original_request = requests.Session.request
    def patched_request(self, method, url, *args, **kwargs):
        kwargs.setdefault('verify', False)
        return original_request(self, method, url, *args, **kwargs)
    
    requests.Session.request = patched_request
    
    # 기본 세션 설정
    default_session = requests.Session()
    default_session.verify = False
    requests.session = lambda: default_session

def patch_httpx():
    """httpx 패치 (선택적)"""
    try:
        import httpx
        original_httpx_init = httpx.Client.__init__
        
        def patched_httpx_init(self, *args, **kwargs):
            kwargs['verify'] = False
            original_httpx_init(self, *args, **kwargs)
        
        httpx.Client.__init__ = patched_httpx_init
    except ImportError:
        raise ImportError("httpx 모듈을 찾을 수 없습니다.")

def patch_huggingface():
    """huggingface_hub 패치 (선택적)"""
    try:
        # 모든 huggingface_hub 관련 모듈에 대한 패치
        import huggingface_hub
        from huggingface_hub.file_download import _request_wrapper
        import huggingface_hub.utils._http

        # 파일 다운로드 요청 래퍼 패치
        original_hf_request_wrapper = _request_wrapper
        
        def patched_hf_request_wrapper(*args, **kwargs):
            if isinstance(kwargs, dict):
                kwargs['verify'] = False
            return original_hf_request_wrapper(*args, **kwargs)
        
        patched_hf_request_wrapper.__signature__ = inspect.signature(original_hf_request_wrapper)
        huggingface_hub.file_download._request_wrapper = patched_hf_request_wrapper
        
        # HTTP 세션 생성 패치
        if hasattr(huggingface_hub.utils._http, "create_http_session"):
            original_create_session = huggingface_hub.utils._http.create_http_session
            
            def patched_create_session(*args, **kwargs):
                kwargs["verify"] = False
                session = original_create_session(*args, **kwargs)
                session.verify = False
                return session
            
            huggingface_hub.utils._http.create_http_session = patched_create_session
            
        # 기본 세션 패치
        if hasattr(huggingface_hub.utils._http, "get_session"):
            original_get_session = huggingface_hub.utils._http.get_session
            
            def patched_get_session(*args, **kwargs):
                session = original_get_session(*args, **kwargs)
                session.verify = False
                return session
            
            huggingface_hub.utils._http.get_session = patched_get_session

    except ImportError:
        raise ImportError("huggingface_hub 모듈을 찾을 수 없습니다.")
    except AttributeError as e:
        # 버전이 다른 경우 패치가 실패할 수 있음
        print(f"[SSL 패치] huggingface_hub 패치 부분 실패 (새 버전과 호환되지 않을 수 있음): {e}")

def patch_transformers():
    """transformers 패치 (선택적)"""
    try:
        import transformers.utils.hub
        
        original_cached_file = transformers.utils.hub.cached_file
        
        def patched_cached_file(*args, **kwargs):
            if 'local_files_only' not in kwargs:
                kwargs['local_files_only'] = False
            # Force 옵션이 있으면 항상 True로 설정
            if 'force_download' in kwargs:
                kwargs['force_download'] = True
            return original_cached_file(*args, **kwargs)
        
        transformers.utils.hub.cached_file = patched_cached_file
        
        # HTTP 세션 패치 (transformers가 직접 http 요청하는 경우)
        if hasattr(transformers.utils, "http"):
            if hasattr(transformers.utils.http, "get_session"):
                original_get_session = transformers.utils.http.get_session
                
                def patched_get_session(*args, **kwargs):
                    session = original_get_session(*args, **kwargs)
                    session.verify = False
                    return session
                
                transformers.utils.http.get_session = patched_get_session
        
    except ImportError:
        raise ImportError("transformers 모듈을 찾을 수 없습니다.")

# SSL 관련 컨텍스트 관리자
def no_ssl_verification_httpx():
    """httpx의 SSL 인증 검사를 비활성화하는 컨텍스트 관리자"""
    import contextlib
    import httpx
    
    @contextlib.contextmanager
    def manager():
        original_init = httpx.Client.__init__
        
        def new_init(self, *args, **kwargs):
            kwargs['verify'] = False
            original_init(self, *args, **kwargs)
        
        httpx.Client.__init__ = new_init
        try:
            yield
        finally:
            httpx.Client.__init__ = original_init
    
    return manager()

def no_ssl_verification_requests():
    """requests의 SSL 인증 검사를 비활성화하는 컨텍스트 관리자"""
    import contextlib
    import requests
    
    @contextlib.contextmanager
    def manager():
        original_request = requests.Session.request
        
        def new_request(self, method, url, *args, **kwargs):
            kwargs.setdefault("verify", False)
            return original_request(self, method, url, *args, **kwargs)
        
        try:
            requests.Session.request = new_request
            yield
        finally:
            requests.Session.request = original_request
    
    return manager()

# 모듈 초기화 시 SSL 패치 적용
if __name__ == "__main__":
    init_ssl_patch()
    patch_ssl_modules() 