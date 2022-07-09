from django_filters import FilterSet, DateFilter
from django.forms import DateInput
from .models import Appointment


class AppointmentFilter(FilterSet):
    dapp = DateFilter(widget=DateInput(format='%Y-%m-%d',
                                       attrs={'class': 'form-control datetimepicker-input', 'type': 'date'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters['specname'].extra.update({'empty_label': 'Специализация'})


    class Meta:
        model = Appointment
        fields = ['dapp', 'specname']
