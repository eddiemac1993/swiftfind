# forms.py
from django import forms
from .models import Animals, VaccinationRecord, Equipment, MaintenanceLog, StockItem, StockTransaction, Employee, EmployeeAttendance, EmployeeEquipment, EquipmentDamageReport

class AnimalForm(forms.ModelForm):
    class Meta:
        model = Animals
        fields = ['tag_number', 'name', 'breed', 'color', 'date_of_birth', 'health_status', 'last_vaccinated', 'weight', 'notes']

    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    last_vaccinated = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

class VaccinationRecordForm(forms.ModelForm):
    class Meta:
        model = VaccinationRecord
        fields = '__all__'

class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = '__all__'

class MaintenanceLogForm(forms.ModelForm):
    class Meta:
        model = MaintenanceLog
        fields = '__all__'

class StockItemForm(forms.ModelForm):
    class Meta:
        model = StockItem
        fields = '__all__'

class StockTransactionForm(forms.ModelForm):
    class Meta:
        model = StockTransaction
        fields = '__all__'

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = '__all__'

class EmployeeAttendanceForm(forms.ModelForm):
    class Meta:
        model = EmployeeAttendance
        fields = '__all__'

class EmployeeEquipmentForm(forms.ModelForm):
    class Meta:
        model = EmployeeEquipment
        fields = '__all__'

class EquipmentDamageReportForm(forms.ModelForm):
    class Meta:
        model = EquipmentDamageReport
        fields = '__all__'