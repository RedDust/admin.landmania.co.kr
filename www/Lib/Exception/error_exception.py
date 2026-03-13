class ErrorPageException(Exception):
    """랜드매니아 공통 에러 처리를 위한 커스텀 예외"""
    def __init__(self, title, message, path=None, line_no=None):
        self.title = title
        self.message = message
        self.path = path
        self.line_no = line_no
        super().__init__(message)