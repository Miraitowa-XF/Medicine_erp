from django import forms
from django.forms import inlineformset_factory
from .models import (
    PurchaseOrder, SalesOrder, PurchaseDetail, SalesDetail,
    PurchaseReturnOrder, SalesReturnOrder, PurchaseReturnDetail, SalesReturnDetail
)

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

class PurchaseReturnOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseReturnOrder
        fields = ['supplier', 'return_date', 'status']
        widgets = {
            'return_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class SalesReturnOrderForm(forms.ModelForm):
    class Meta:
        model = SalesReturnOrder
        fields = ['customer', 'return_date', 'status']
        widgets = {
            'return_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
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

class PurchaseReturnDetailForm(forms.ModelForm):
    class Meta:
        model = PurchaseReturnDetail
        fields = ['inventory', 'quantity', 'unit_price']

class SalesReturnDetailForm(forms.ModelForm):
    class Meta:
        model = SalesReturnDetail
        fields = ['inventory', 'quantity', 'refund_price']

PurchaseDetailFormSet = inlineformset_factory(
    PurchaseOrder, PurchaseDetail, form=PurchaseDetailForm,
    extra=1, can_delete=True
)

SalesDetailFormSet = inlineformset_factory(
    SalesOrder, SalesDetail, form=SalesDetailForm,
    extra=1, can_delete=True
)

PurchaseReturnDetailFormSet = inlineformset_factory(
    PurchaseReturnOrder, PurchaseReturnDetail, form=PurchaseReturnDetailForm,
    extra=1, can_delete=True
)

SalesReturnDetailFormSet = inlineformset_factory(
    SalesReturnOrder, SalesReturnDetail, form=SalesReturnDetailForm,
    extra=1, can_delete=True
)
