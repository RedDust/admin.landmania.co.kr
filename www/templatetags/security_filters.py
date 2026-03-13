import bleach
from bleach.css_sanitizer import CSSSanitizer
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def sanitize(value):
    if not value:
        return ""

    # 1. 허용할 태그 리스트 (게시판 본문에 꼭 필요한 것 위주로 정리)
    # 레이아웃을 해칠 수 있는 header, nav, section, article, main, button은 제외했습니다.
    allowed_tags = [
        'p', 'b', 'i', 'u', 'strong', 'em', 'a', 'img', 'span', 'br',
        'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'table', 'thead', 'tbody', 'tr', 'th', 'td', 'blockquote', 'pre', 'code', 'div'
    ]

    # 2. 허용할 속성 (태그별로 정밀하게 설정)
    allowed_attrs = {
        'a': ['href', 'title', 'target', 'rel'],
        'img': ['src', 'alt', 'title', 'width', 'height', 'style'],
        'span': ['style', 'class'],
        'div': ['style', 'class'],
        '*': ['class'],  # 모든 태그에 공통으로 class 허용
    }

    # 3. 허용할 CSS 속성 (style 태그를 통해 XSS가 발생하는 것을 방지)
    # 에디터에서 글자 색상, 배경색, 정렬 등을 쓸 때 필요합니다.
    css_sanitizer = CSSSanitizer(allowed_css_properties=[
        'color', 'background-color', 'font-size', 'font-weight', 
        'text-align', 'text-decoration', 'width', 'height', 'padding', 'margin'
    ])

    # 4. 세정 작업
    cleaned_html = bleach.clean(
        value,
        tags=allowed_tags,
        attributes=allowed_attrs,
        css_sanitizer=css_sanitizer,
        protocols=['http', 'https', 'mailto'], # javascript: 프로토콜 차단
        strip=True # 허용되지 않은 태그는 아예 제거 (엔티티 변환 대신 삭제)
    )

    # 5. 장고 템플릿에서 HTML로 인식하도록 mark_safe 처리
    return mark_safe(cleaned_html)