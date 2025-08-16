from django import forms
from .models import CV

class CVForm(forms.ModelForm):
    class Meta:
        model = CV
        fields = '__all__'
        exclude = ['user', 'template']  # exclude fields set programmatically
        widgets = {
            'full_name': forms.TextInput(attrs={
                'placeholder': 'John Doe',
                'class': 'form-control'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'john.doe@example.com',
                'class': 'form-control'
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': '+1 (555) 123-4567',
                'class': 'form-control'
            }),
            'address': forms.Textarea(attrs={
                'placeholder': '123 Main Street, Apt 4B\nNew York, NY 10001',
                'class': 'form-control',
                'rows': 3
            }),
            'website': forms.URLInput(attrs={
                'placeholder': 'https://yourportfolio.com',
                'class': 'form-control'
            }),
            'professional_summary': forms.Textarea(attrs={
                'placeholder': 'Experienced software engineer with 5+ years in web development...\n'
                               'Specialized in Django, React, and cloud technologies...\n'
                               'Passionate about creating efficient, scalable solutions...',
                'class': 'form-control',
                'rows': 5
            }),
            'key_skills': forms.Textarea(attrs={
                'placeholder': '- Python (Django, Flask)\n'
                               '- JavaScript (React, Node.js)\n'
                               '- Database Design (PostgreSQL, MySQL)\n'
                               '- Cloud Services (AWS, Docker)\n'
                               '- Agile Methodologies',
                'class': 'form-control',
                'rows': 5
            }),
            'work_experience': forms.Textarea(attrs={
                'placeholder': 'Senior Software Engineer\n'
                               'Tech Company Inc. | Jan 2020 - Present\n'
                               '- Lead development of web applications using Django\n'
                               '- Optimized database queries improving performance by 40%\n'
                               '- Mentored junior developers\n\n'
                               'Software Developer\n'
                               'Startup Co. | May 2018 - Dec 2019\n'
                               '- Built REST APIs for mobile applications\n'
                               '- Implemented CI/CD pipelines',
                'class': 'form-control',
                'rows': 8
            }),
            'education': forms.Textarea(attrs={
                'placeholder': 'B.S. in Computer Science\n'
                               'University of Technology | 2014 - 2018\n'
                               '- GPA: 3.8/4.0\n'
                               '- Relevant coursework: Algorithms, Database Systems\n\n'
                               'Certification in Web Development\n'
                               'Online Institute | 2019',
                'class': 'form-control',
                'rows': 6
            }),
            'certifications': forms.Textarea(attrs={
                'placeholder': '- AWS Certified Developer - Associate (2022)\n'
                               '- Google Professional Data Engineer (2021)\n'
                               '- Scrum Master Certification (2020)',
                'class': 'form-control',
                'rows': 3
            }),
            'languages': forms.Textarea(attrs={
                'placeholder': '- English (Fluent)\n'
                               '- Spanish (Intermediate)\n'
                               '- French (Basic)',
                'class': 'form-control',
                'rows': 3
            }),
            'projects': forms.Textarea(attrs={
                'placeholder': 'E-commerce Platform (2023)\n'
                               '- Built with Django and React\n'
                               '- Integrated payment processing\n\n'
                               'Task Management App (2022)\n'
                               '- Real-time updates with WebSockets\n'
                               '- Deployed on AWS',
                'class': 'form-control',
                'rows': 6
            }),
            'references': forms.Textarea(attrs={
                'placeholder': 'Available upon request\n\n'
                               'OR\n\n'
                               'Dr. Jane Smith\n'
                               'Professor, University of Tech\n'
                               'j.smith@university.edu | (555) 987-6543\n\n'
                               'Mr. Robert Johnson\n'
                               'CTO, Tech Company Inc.\n'
                               'r.johnson@company.com | (555) 123-4567',
                'class': 'form-control',
                'rows': 8
            }),
        }
