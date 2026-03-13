import inspect

def _lineno():
    """현재 호출된 위치의 라인 번호를 안전하게 반환합니다."""
    frame = inspect.currentframe()
    
    # currentframe()이 None인지 먼저 확인합니다.
    if frame is not None and frame.f_back is not None:
        return frame.f_back.f_lineno
    
    return 0  # 프레임을 찾을 수 없는 경우 기본값 반환