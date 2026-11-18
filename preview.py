"""PART 3 - Markdown live preview engine (Member 3).

* render_markdown_html(text)  : Markdown -> HTML, plus [flow] and [math] shortcodes
                               (pure Python, no GUI - easy to unit-test)
* PreviewMixin                : pushes that HTML into the QWebEngineView and keeps
                               the preview scrolled in sync with the editor
"""
import os
import re
import markdown
from PyQt6.QtCore import QUrl


PREVIEW_CSS = """
html { scroll-behavior: smooth; }
body {
    margin: 0;
    padding: 24px 28px 40px 28px;
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    font-size: 15px;
    line-height: 1.7;
    color: #1f2937;
    background: #ffffff;
}
h1, h2, h3, h4 { color: #111827; font-weight: 700; line-height: 1.3; margin: 1.5em 0 0.6em 0; }
h1 { font-size: 28px; padding-bottom: 0.3em; border-bottom: 2px solid #e5e7eb; }
h2 { font-size: 22px; padding-bottom: 0.25em; border-bottom: 1px solid #e5e7eb; }
h3 { font-size: 18px; }
h4 { font-size: 16px; }
p { margin: 0 0 14px 0; }
a { color: #4f46e5; text-decoration: none; }
ul, ol { padding-left: 24px; margin: 0 0 14px 0; }
li { margin-bottom: 4px; }
hr { border: none; border-top: 1px solid #e5e7eb; margin: 28px 0; }

p:has(img) {
    text-align: center;
    margin: 22px 0;
    background: #f9fafb;
    padding: 14px;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
}
img {
    max-width: 80%;
    max-height: 400px;
    height: auto;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    display: block;
    margin: 0 auto;
}
figcaption {
    font-size: 13px;
    color: #6b7280;
    margin-top: 8px;
    font-style: italic;
    text-align: center;
}

code {
    background: #f3f4f6;
    color: #be185d;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'Cascadia Code', Consolas, monospace;
    font-size: 88%;
}
pre {
    background: #0f172a;
    color: #e2e8f0;
    padding: 14px 16px;
    border-radius: 10px;
    overflow-x: auto;
    font-family: 'Cascadia Code', Consolas, monospace;
    font-size: 13px;
    line-height: 1.5;
}
pre code { background: none; color: inherit; padding: 0; font-size: 100%; }

blockquote {
    border-left: 4px solid #6366f1;
    background: #f8fafc;
    margin: 16px 0;
    padding: 10px 16px;
    color: #475569;
    border-radius: 0 8px 8px 0;
}
blockquote p:last-child { margin-bottom: 0; }

table { border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 14px; }
th, td { border: 1px solid #e5e7eb; padding: 8px 12px; text-align: left; }
th { background: #f9fafb; font-weight: 600; }
tr:nth-child(even) td { background: #fcfcfd; }
"""

PREVIEW_SHELL = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>__CSS__</style>
</head>
<body>
    <div id="content"></div>
</body>
</html>
""".replace("__CSS__", PREVIEW_CSS)


def render_markdown_html(text):
    """Convert note text (Markdown + shortcodes) to an HTML string."""
    html_body = markdown.markdown(text, extensions=['fenced_code', 'tables', 'nl2br'])

    # 2. Process [flow] shortcode after Markdown conversion
    def replace_flow(match):
        content = match.group(1).strip()
        items = [re.sub(r'<[^>]+>', '', item).strip() for item in re.split(r'<br\s*/?>|\n', content) if item.strip()]
        flow_html = '<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; margin: 25px 0; font-family: \'Segoe UI\', sans-serif;">'
        for i, item in enumerate(items):
            flow_html += f'<div style="font-weight: 600; font-size: 16px; color: #111827; text-align: center; padding: 8px 18px; background: #eef2ff; border-radius: 8px;">{item}</div>'
            if i < len(items) - 1:
                flow_html += '<div style="font-size: 20px; color: #6366f1; margin: 4px 0; text-align: center; line-height: 1;">↓</div>'
        flow_html += '</div>'
        return flow_html

    # 3. Process [math] shortcode after Markdown conversion
    def replace_math(match):
        content = match.group(1).strip()
        clean_content = re.sub(r'<[^>]+>', '', content)

        if '=' in clean_content:
            left, right = clean_content.split('=', 1)
            left = left.strip()
            right = right.strip()
        else:
            left, right = "", clean_content

        if '/' in right:
            num, den = right.split('/', 1)
            num = num.strip().strip('()')
            den = den.strip().strip('()')

            return f'''
            <div style="display: flex; align-items: center; justify-content: center; font-family: 'Times New Roman', serif; font-size: 18px; font-style: italic; margin: 18px 0;">
                {f"<span>{left} &nbsp;=&nbsp;</span>" if left else ""}
                <div style="display: inline-flex; flex-direction: column; align-items: center; text-align: center; padding: 0 4px;">
                    <span style="border-bottom: 1.5px solid #111827; padding: 0 8px 2px 8px; width: 100%; text-align: center;">{num}</span>
                    <span style="padding: 2px 8px 0 8px; width: 100%; text-align: center;">{den}</span>
                </div>
            </div>
            '''
        else:
            return f'<div style="text-align: center; font-size: 18px; margin: 15px 0;"><i>{clean_content}</i></div>'

    # 4. Replace shortcodes on HTML text
    html_body = re.sub(r'\[flow\](.*?)\[/flow\]', replace_flow, html_body, flags=re.DOTALL | re.IGNORECASE)
    html_body = re.sub(r'\[math\](.*?)\[/math\]', replace_math, html_body, flags=re.DOTALL | re.IGNORECASE)
    return html_body


class PreviewMixin:
    def setup_initial_preview_html(self):
        base_path = QUrl.fromLocalFile(os.getcwd() + "/")
        self.preview_view.setHtml(PREVIEW_SHELL, baseUrl=base_path)

    def sync_scroll_with_cursor(self):
        editor_scroll = self.editor.verticalScrollBar()
        if editor_scroll.maximum() > 0:
            ratio = editor_scroll.value() / editor_scroll.maximum()
            js_script = f"""
            var maxScroll = document.documentElement.scrollHeight - window.innerHeight;
            if (maxScroll > 0) {{
                window.scrollTo({{ top: maxScroll * {ratio}, behavior: 'smooth' }});
            }}
            """
            self.preview_view.page().runJavaScript(js_script)

    def update_live_preview(self):
        text = self.editor.toPlainText()
        html_body = render_markdown_html(text)

        # Escape for a JavaScript template literal. Newlines are kept so code blocks keep their line breaks.
        escaped_html = (
            html_body.replace('\r', '')
            .replace('\\', '\\\\')
            .replace('`', '\\`')
            .replace('$', '\\$')
        )

        js_update = f"""
        document.getElementById('content').innerHTML = `{escaped_html}`;

        document.querySelectorAll('#content img').forEach((img, index) => {{
            if (!img.nextElementSibling || img.nextElementSibling.tagName !== 'FIGCAPTION') {{
                const caption = document.createElement('figcaption');
                const altText = img.getAttribute('alt') || 'Figure';
                caption.innerText = `Figure ${{index + 1}}: ${{altText}}`;
                img.after(caption);
            }}
        }});
        """
        self.preview_view.page().runJavaScript(js_update)
        self.sync_scroll_with_cursor()
