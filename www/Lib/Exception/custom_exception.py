class CustomException(Exception):
    def __init__(self, title, message, path, line_no):
        self.title = title
        self.message = message
        self.path = path
        self.line_no = line_no
        # 부모 클래스(Exception)에도 기본 메시지 전달
        super().__init__(message)

    def __str__(self):
        return f"[{self.title}] at {self.path} (line {self.line_no}): {self.message}"
    

class RedirectMessageException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)