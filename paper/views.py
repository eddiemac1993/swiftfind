from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from .models import Paper, PaperItem
from .forms import PaperForm, PaperItemForm
from django.contrib import messages


def create_paper(request):
    if request.method == 'POST':
        paper_form = PaperForm(request.POST, request.FILES)  # Include request.FILES for file uploads
        if paper_form.is_valid():
            try:
                # Save the paper
                paper = paper_form.save()

                # Redirect to the add_items page for this paper
                messages.success(request, "Paper created successfully. You can now add items.")
                return redirect('add_items', paper_id=paper.id)

            except Exception as e:
                # Log the error and display a message to the user
                messages.error(request, f"An error occurred: {str(e)}")
        else:
            # Print form errors to the console for debugging
            print(paper_form.errors)
            # Display form errors to the user
            messages.error(request, "Please correct the errors below.")
    else:
        paper_form = PaperForm()

    context = {
        'paper_form': paper_form,
    }
    return render(request, 'paper/create_paper.html', context)


# Add Items to Paper
def add_items(request, paper_id):
    paper = get_object_or_404(Paper, id=paper_id)

    if request.method == 'POST':
        # Get the item_id from the form (default to None if not provided or empty)
        item_id = request.POST.get('item_id') or None

        if item_id:  # Editing an existing item
            try:
                item = get_object_or_404(PaperItem, id=item_id, paper=paper)
                form = PaperItemForm(request.POST, instance=item)
            except ValueError:
                # Handle invalid item_id (e.g., non-numeric value)
                messages.error(request, "Invalid item ID.")
                return redirect('add_items', paper_id=paper.id)
        else:  # Adding a new item
            form = PaperItemForm(request.POST)

        if form.is_valid():
            item = form.save(commit=False)
            item.paper = paper
            item.save()
            messages.success(request, "Item saved successfully.")
            return redirect('add_items', paper_id=paper.id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PaperItemForm()

    # Fetch all items for the paper and calculate the total
    items = paper.items.all()
    total = sum(item.total_price for item in items)

    context = {
        'form': form,
        'paper': paper,
        'items': items,
        'total': total,
    }
    return render(request, 'paper/add_items.html', context)


# View Paper
def view_paper(request, paper_id):
    paper = get_object_or_404(Paper, id=paper_id)
    items = paper.items.all()

    # Calculate the grand total
    grand_total = sum(item.total_price for item in items)

    context = {
        'paper': paper,
        'items': items,
        'grand_total': grand_total,  # Pass the grand total to the template
    }
    return render(request, 'paper/view_paper.html', context)


# Edit Item
def edit_item(request, item_id):
    item = get_object_or_404(PaperItem, id=item_id)
    if request.method == 'POST':
        form = PaperItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('add_items', paper_id=item.paper.id)
    else:
        form = PaperItemForm(instance=item)

    context = {
        'form': form,
        'item': item,
    }
    return render(request, 'paper/edit_item.html', context)


# Delete Item
def delete_item(request, item_id):
    item = get_object_or_404(PaperItem, id=item_id)
    paper_id = item.paper.id
    item.delete()
    return redirect('add_items', paper_id=paper_id)


# Download Paper as PDF
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML
from .models import Paper, PaperItem

from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.http import HttpResponse
from xhtml2pdf import pisa
from .models import Paper, PaperItem
import os

def download_paper(request, paper_id):
    # Fetch the paper object
    paper = get_object_or_404(Paper, id=paper_id)

    # Debug: Print the logo URL
    if paper.logo:
        print(f"Logo URL: {paper.logo.url}")
    else:
        print("No logo found for this paper.")

    # Fetch items for the paper
    items = paper.items.all()

    # Calculate the grand total
    grand_total = sum(item.total_price for item in items)

    # Render the HTML template
    html_string = render_to_string('paper/paper_pdf_template.html', {
        'paper': paper,
        'items': items,
        'grand_total': grand_total,
    })

    # Debug: Print the HTML string
    print(html_string)

    # Generate PDF using xhtml2pdf
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{paper.paper_number}.pdf"'

    # Convert HTML to PDF
    pdf_status = pisa.CreatePDF(html_string, dest=response)

    # Check for errors
    if pdf_status.err:
        return HttpResponse('An error occurred while generating the PDF.')

    return response