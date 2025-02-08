from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Sum

class Farm(models.Model):
    """A model representing a farm owned by a user."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='farms')
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name} - {self.user.username}"

    def total_animals(self):
        """Returns the total number of animals on the farm."""
        return self.farm_animals.count()

    def total_crops(self):
        """Returns the total number of crops on the farm."""
        return self.crops.count()

    def clean(self):
        """Ensures the farm size is a positive value."""
        if self.size <= 0:
            raise ValidationError("Farm size must be a positive value.")

class Animals(models.Model):
    HEALTH_STATUS_CHOICES = [
        ('Healthy', 'Healthy'),
        ('Sick', 'Sick'),
        ('Injured', 'Injured'),
        ('Quarantined', 'Quarantined'),
    ]

    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='farm_animals')
    tag_number = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    breed = models.CharField(max_length=100)
    color = models.CharField(max_length=50)
    date_of_birth = models.DateField(null=True, blank=True)
    health_status = models.CharField(max_length=50, choices=HEALTH_STATUS_CHOICES, default='Healthy')
    last_vaccinated = models.DateField(null=True, blank=True)
    weight = models.FloatField()
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.tag_number} - {self.name}"

    def update_health_status(self, new_status):
        """Updates the health status of the animal."""
        if new_status in dict(self.HEALTH_STATUS_CHOICES):
            self.health_status = new_status
            self.save()
        else:
            raise ValueError("Invalid health status")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['farm', 'tag_number'], name='unique_farm_animal_tag')
        ]


class Crop(models.Model):
    """A model for tracking crops grown on the farm."""
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='crops')
    name = models.CharField(max_length=100)
    planted_date = models.DateField()
    harvest_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=100, choices=[('Growing', 'Growing'), ('Harvested', 'Harvested')])

    def __str__(self):
        return f"{self.name} - {self.status}"

class VaccinationRecord(models.Model):
    """Tracks vaccination records for animals."""
    animal = models.ForeignKey(Animals, on_delete=models.CASCADE, related_name='vaccinations')
    vaccine_name = models.CharField(max_length=100)
    date_administered = models.DateField()
    next_due_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.animal.name} - {self.vaccine_name}"

    def clean(self):
        """Ensures the next due date is after the date administered."""
        if self.next_due_date and self.next_due_date <= self.date_administered:
            raise ValidationError("Next due date must be after the date administered.")


class EquipmentCategory(models.Model):
    """Represents categories for farm equipment."""
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Equipment(models.Model):
    CONDITION_CHOICES = [
        ('New', 'New'),
        ('Good', 'Good'),
        ('Needs Repair', 'Needs Repair'),
        ('Broken', 'Broken'),
    ]

    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='farm_equipment')
    name = models.CharField(max_length=255)
    category = models.ForeignKey(EquipmentCategory, on_delete=models.CASCADE)
    brand = models.CharField(max_length=255)
    purchase_date = models.DateField()
    condition = models.CharField(max_length=50, choices=CONDITION_CHOICES)
    quantity = models.PositiveIntegerField()
    location = models.CharField(max_length=255)
    notes = models.TextField(blank=True, default="")

    def __str__(self):
        return f"{self.name} - {self.brand}"

    def clean(self):
        """Ensures the purchase date is not in the future."""
        if self.purchase_date > timezone.now().date():
            raise ValidationError("Purchase date cannot be in the future.")


class MaintenanceLog(models.Model):
    """Tracks maintenance and repair history for equipment."""
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='maintenance_logs')
    maintenance_date = models.DateField()
    description = models.TextField()
    cost = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.equipment.name} - {self.maintenance_date}"


class StockCategory(models.Model):
    """Represents categories for stock items."""
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class StockItem(models.Model):
    """Represents stock items like feed, medicine, etc."""
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='stock_items')
    category = models.ForeignKey(StockCategory, on_delete=models.PROTECT)
    name = models.CharField(max_length=100)
    quantity = models.FloatField(default=0)  # Supports liquids & kg
    unit = models.CharField(max_length=10, choices=[('kg', 'Kilograms'), ('L', 'Liters')])
    in_stock = models.FloatField(default=0)  # Track stock added
    out_stock = models.FloatField(default=0)  # Track stock used

    def remaining_stock(self):
        """Calculates the remaining stock."""
        return round(max(0, self.in_stock - self.out_stock), 2)

    def add_stock(self, amount):
        """Adds stock to the item."""
        if amount < 0:
            raise ValueError("Amount to add must be positive")
        self.in_stock += amount
        self.save()

    def remove_stock(self, amount):
        """Removes stock from the item."""
        if amount < 0:
            raise ValueError("Amount to remove must be positive")
        if amount > self.remaining_stock():
            raise ValueError("Not enough stock to remove")
        self.out_stock += amount
        self.save()

    def is_stock_low(self, threshold):
        """Checks if the stock is below a given threshold."""
        return self.remaining_stock() < threshold

    def __str__(self):
        return f"{self.name} ({self.remaining_stock()} {self.unit})"

    class Meta:
        verbose_name = "Stock Item"
        verbose_name_plural = "Stock Items"


class StockTransaction(models.Model):
    """Tracks stock transactions (additions and removals)."""
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=[('IN', 'In'), ('OUT', 'Out')])
    quantity = models.FloatField()
    transaction_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.stock_item.name} - {self.transaction_type} ({self.quantity})"


class Employee(models.Model):
    DEPARTMENT_CHOICES = [
        ('Management', 'Management'),
        ('Maintenance', 'Maintenance'),
        ('Veterinary', 'Veterinary'),
        ('Operations', 'Operations'),
    ]
    name = models.CharField(max_length=255)
    department = models.CharField(max_length=255, choices=DEPARTMENT_CHOICES)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Employee"
        verbose_name_plural = "Employees"

class EmployeeAttendance(models.Model):
    """Tracks employee attendance and working hours."""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendance')
    date = models.DateField()
    hours_worked = models.FloatField()

    def __str__(self):
        return f"{self.employee.name} - {self.date} ({self.hours_worked} hrs)"

class EmployeeEquipment(models.Model):
    CONDITION_CHOICES = [
        ('New', 'New'),
        ('Good', 'Good'),
        ('Needs Repair', 'Needs Repair'),
        ('Broken', 'Broken'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    date_issued = models.DateTimeField(auto_now_add=True)
    return_date = models.DateField(null=True, blank=True)
    condition = models.CharField(max_length=50, choices=CONDITION_CHOICES, default='Good')

    def __str__(self):
        return f"{self.employee.name} - {self.equipment.name}"

    def mark_for_repair(self):
        """Marks the equipment as needing repair."""
        self.condition = 'Needs Repair'
        self.save()

    def return_equipment(self):
        """Records the return of the equipment."""
        self.return_date = timezone.now().date()
        self.save()

    class Meta:
        verbose_name = "Employee Equipment"
        verbose_name_plural = "Employee Equipment"


class EquipmentDamageReport(models.Model):
    """Tracks damage reports for equipment issued to employees."""
    employee_equipment = models.ForeignKey(EmployeeEquipment, on_delete=models.CASCADE, related_name='damage_reports')
    description = models.TextField()
    reported_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee_equipment} - {self.reported_date}"