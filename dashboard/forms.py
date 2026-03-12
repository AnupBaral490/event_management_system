from django import forms

from bookings.models import Coupon
from events.models import Event, EventTicketType


class OrganizerTicketTypeForm(forms.ModelForm):
    class Meta:
        model = EventTicketType
        fields = [
            'event',
            'name',
            'description',
            'price',
            'quantity',
            'sale_start',
            'sale_end',
            'status',
            'is_active',
        ]
        widgets = {
            'sale_start': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'sale_end': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        organizer = kwargs.pop('organizer', None)
        super().__init__(*args, **kwargs)
        if organizer is not None:
            self.fields['event'].queryset = Event.objects.filter(organizer=organizer).order_by('start_datetime')
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            else:
                existing = field.widget.attrs.get('class', '')
                field.widget.attrs['class'] = f"{existing} form-control".strip()
        self.fields['sale_start'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['sale_end'].input_formats = ['%Y-%m-%dT%H:%M']


class OrganizerCouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = [
            'code',
            'event',
            'description',
            'discount_type',
            'discount_value',
            'max_discount_amount',
            'min_order_amount',
            'max_total_uses',
            'max_uses_per_user',
            'valid_from',
            'valid_until',
            'is_active',
        ]
        widgets = {
            'valid_from': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'valid_until': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        organizer = kwargs.pop('organizer', None)
        super().__init__(*args, **kwargs)
        self.fields['event'].required = False
        if organizer is not None:
            self.fields['event'].queryset = Event.objects.filter(organizer=organizer).order_by('start_datetime')
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            else:
                existing = field.widget.attrs.get('class', '')
                field.widget.attrs['class'] = f"{existing} form-control".strip()
        self.fields['valid_from'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['valid_until'].input_formats = ['%Y-%m-%dT%H:%M']
