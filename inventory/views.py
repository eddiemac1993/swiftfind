# views.py
from django.shortcuts import render, get_object_or_404, redirect
from .models import Farm, Animals, Crop, StockItem, Employee, EmployeeAttendance
from .forms import AnimalForm, EquipmentForm, StockItemForm, EmployeeForm
from directory.models import Business
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum

@login_required
def dashboard(request):
    """View that provides summary data for the farm dashboard."""
    # Get the user's farm(s)
    farms = Farm.objects.filter(user=request.user)

    # Initialize variables to hold totals
    total_animals = 0
    total_crops = 0
    total_stock_value = 0
    total_employees = 0
    total_attendance_hours = 0

    # Iterate over each farm to gather totals
    for farm in farms:
        total_animals += farm.total_animals()  # total animals on the farm
        total_crops += farm.total_crops()  # total crops on the farm
        # Calculate the total stock value on the farm (if needed)
        for stock_item in farm.stock_items.all():
            total_stock_value += stock_item.remaining_stock()  # Assuming 'remaining_stock' is a numeric value

        # Calculate employee stats for this farm
        total_employees += farm.user.employees.count()  # Assuming the user is linked to employees
        # Calculate total hours worked by employees for this farm (if needed)
        for employee in farm.user.employees.all():
            total_attendance_hours += employee.attendance.aggregate(Sum('hours_worked'))['hours_worked__sum'] or 0

    # Prepare context data for rendering
    context = {
        'farms': farms,
        'total_animals': total_animals,
        'total_crops': total_crops,
        'total_stock_value': total_stock_value,
        'total_employees': total_employees,
        'total_attendance_hours': total_attendance_hours,
    }

    return render(request, 'dashboard.html', context)

@login_required
def add_animal(request):
    if request.method == "POST":
        form = AnimalForm(request.POST, request.FILES)
        if form.is_valid():
            animal = form.save(commit=False)
            animal.business = request.user  # Assign the logged-in user
            animal.save()
            return redirect("animal_list")  # Redirect to the animal list page
    else:
        form = AnimalForm()

    return render(request, "add_animal.html", {"form": form})

def manage_equipment(request):
    equipment_list = Equipment.objects.all()
    return render(request, 'manage_equipment.html', {'equipment_list': equipment_list})

def add_equipment(request):
    if request.method == 'POST':
        form = EquipmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_equipment')
    else:
        form = EquipmentForm()
    return render(request, 'add_equipment.html', {'form': form})

def edit_equipment(request, pk):
    equipment = get_object_or_404(Equipment, pk=pk)
    if request.method == 'POST':
        form = EquipmentForm(request.POST, instance=equipment)
        if form.is_valid():
            form.save()
            return redirect('manage_equipment')
    else:
        form = EquipmentForm(instance=equipment)
    return render(request, 'edit_equipment.html', {'form': form})

def delete_equipment(request, pk):
    equipment = get_object_or_404(Equipment, pk=pk)
    if request.method == 'POST':
        equipment.delete()
        return redirect('manage_equipment')
    return render(request, 'delete_equipment.html', {'equipment': equipment})

def stock_management(request):
    stock_items = StockItem.objects.all()
    return render(request, 'stock_management.html', {'stock_items': stock_items})

def add_stock_item(request):
    if request.method == 'POST':
        form = StockItemForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('stock_management')
    else:
        form = StockItemForm()
    return render(request, 'add_stock_item.html', {'form': form})

def edit_stock_item(request, pk):
    stock_item = get_object_or_404(StockItem, pk=pk)
    if request.method == 'POST':
        form = StockItemForm(request.POST, instance=stock_item)
        if form.is_valid():
            form.save()
            return redirect('stock_management')
    else:
        form = StockItemForm(instance=stock_item)
    return render(request, 'edit_stock_item.html', {'form': form})

def delete_stock_item(request, pk):
    stock_item = get_object_or_404(StockItem, pk=pk)
    if request.method == 'POST':
        stock_item.delete()
        return redirect('stock_management')
    return render(request, 'delete_stock_item.html', {'stock_item': stock_item})

def manage_employees(request):
    employees = Employee.objects.all()
    return render(request, 'manage_employees.html', {'employees': employees})

def add_employee(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_employees')
    else:
        form = EmployeeForm()
    return render(request, 'add_employee.html', {'form': form})

def edit_employee(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            return redirect('manage_employees')
    else:
        form = EmployeeForm(instance=employee)
    return render(request, 'edit_employee.html', {'form': form})

def delete_employee(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        employee.delete()
        return redirect('manage_employees')
    return render(request, 'delete_employee.html', {'employee': employee})