from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
import tempfile
from .models import CVTemplate, CV
from .forms import CVForm

@login_required
def template_selection(request):
    templates = CVTemplate.objects.all()
    return render(request, 'cv_app/template_selection.html', {'templates': templates})

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from .models import CVTemplate
from .forms import CVForm

@login_required
def create_cv(request, template_id):
    template = get_object_or_404(CVTemplate, id=template_id)
    
    if request.method == 'POST':
        form = CVForm(request.POST)
        if form.is_valid():
            cv = form.save(commit=False)
            cv.user = request.user
            cv.template = template
            cv.save()
            return redirect('preview_cv', cv_id=cv.id)
    else:
        form = CVForm()
    
    return render(request, 'cv_app/cv_form.html', {
        'form': form,
        'template': template
    })


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from .models import CV
from .forms import CVForm

@login_required
def preview_cv(request, cv_id):
    cv = get_object_or_404(CV, id=cv_id, user=request.user)

    if request.method == "POST":
        form = CVForm(request.POST, instance=cv)
        if form.is_valid():
            form.save()
            return redirect('preview_cv', cv_id=cv.id)  # refresh page after save
    else:
        form = CVForm(instance=cv)

    template_name = f"cv_app/{cv.template.template_file}"

    context = {
        'form': form,
        'cv': cv,
        'has_personal_info': any([cv.full_name, cv.email, cv.phone, cv.address, cv.website]),
        'has_professional_summary': bool(cv.professional_summary),
        'has_key_skills': bool(cv.key_skills),
        'has_work_experience': bool(cv.work_experience),
        'has_education': bool(cv.education),
        'has_certifications': bool(cv.certifications),
        'has_languages': bool(cv.languages),
        'has_projects': bool(cv.projects),
        'has_references': bool(cv.references),
    }

    return render(request, template_name, context)


@login_required
def download_cv(request, cv_id):
    cv = get_object_or_404(CV, id=cv_id, user=request.user)
    template_name = f"cv_app/{cv.template.template_file}"
    
    # Render HTML with all the context variables
    html_string = render_to_string(template_name, {
        'cv': cv,
        'has_personal_info': any([cv.full_name, cv.email, cv.phone, cv.address, cv.website]),
        'has_professional_summary': bool(cv.professional_summary),
        'has_key_skills': bool(cv.key_skills),
        'has_work_experience': bool(cv.work_experience),
        'has_education': bool(cv.education),
        'has_certifications': bool(cv.certifications),
        'has_languages': bool(cv.languages),
        'has_projects': bool(cv.projects),
        'has_references': bool(cv.references),
    })
    
    # Create PDF
    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    
    # Generate PDF into a temporary file
    result = html.write_pdf()
    
    # Create HTTP response with PDF
    response = HttpResponse(content_type='application/pdf')
    
    # Use the CV's name for the downloaded file
    filename = f"{cv.full_name or 'my_cv'}_CV.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response['Content-Transfer-Encoding'] = 'binary'
    
    # Write the PDF to the response
    with tempfile.NamedTemporaryFile(delete=True) as output:
        output.write(result)
        output.flush()
        output.seek(0)
        response.write(output.read())
    
    return response