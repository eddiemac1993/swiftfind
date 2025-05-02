# widgets.py
from django import forms

class CKEditorCDNWidget(forms.Textarea):
    class Media:
        js = [
            'https://cdn.ckeditor.com/4.25.1-lts/standard/ckeditor.js',
        ]

    def render(self, name, value, attrs=None, renderer=None):
        textarea = super().render(name, value, attrs, renderer)
        return textarea + f'''
        <script>
            if (typeof CKEDITOR !== 'undefined') {{
                CKEDITOR.replace('{attrs["id"]}');
            }}
        </script>
        '''
