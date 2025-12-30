from django import forms
from django.forms import inlineformset_factory
from .models import PurchaseOrder, SalesOrder, PurchaseDetail, SalesDetail

class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['supplier', 'order_date', 'status']
        widgets = {
            'order_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class SalesOrderForm(forms.ModelForm):
    class Meta:
        model = SalesOrder
        fields = ['customer', 'order_date', 'status']
        widgets = {
            'order_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class PurchaseDetailForm(forms.ModelForm):
    class Meta:
        model = PurchaseDetail
        fields = ['medicine', 'batch_number', 'produce_date', 'expiry_date', 'quantity', 'unit_price']
        widgets = {
            'produce_date': forms.DateInput(attrs={'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }

class SalesDetailForm(forms.ModelForm):
    class Meta:
        model = SalesDetail
        fields = ['inventory', 'quantity', 'actual_price']

PurchaseDetailFormSet = inlineformset_factory(
    PurchaseOrder, PurchaseDetail, form=PurchaseDetailForm,
    extra=1, can_delete=True
)

SalesDetailFormSet = inlineformset_factory(
    SalesOrder, SalesDetail, form=SalesDetailForm,
    extra=1, can_delete=True
)
