from django import forms

class EmployeeForm(forms.Form):
    full_name = forms.CharField(label="ФИО сотрудника", max_length=255)
    employee_id = forms.CharField(label="Табельный номер", max_length=20)
    train_number = forms.CharField(label="Поезд", max_length=20)
    wagon_number = forms.CharField(label="Вагон", max_length=20)