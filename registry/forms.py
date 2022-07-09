from dal import autocomplete
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from .models import Appointment, Profile, Booking
import datetime


class BootstrapAuthenticationForm(AuthenticationForm):
    username = forms.CharField(max_length=254,
                               widget=forms.TextInput({'class': 'form-control',
                                                       'placeholder': 'Номер документа (паспорт, СНИЛС)'}))
    password = forms.CharField(label=_("Password"),
                               widget=forms.PasswordInput({'class': 'form-control',
                                                           'placeholder': 'Дата рождения'}))


class AppointmentForm(forms.ModelForm):
    doctor = forms.ModelChoiceField(
        queryset=User.objects.filter(is_staff=False),
        label='Врач',
        widget=autocomplete.ModelSelect2(url='select2_fk_doctor')
    )

    class Meta:
        model = Appointment
        fields = '__all__'

    def clean_dapp(self):
        dapp = self.cleaned_data['dapp']
        if dapp < datetime.date.today():
            raise ValidationError('Прием завершен, редактирование или ввод новой строки приема в прошлом невозможны!',
                                  code='invalid')
        return dapp

    def clean(self):
        cleaned_data = super().clean()
        appbegin = cleaned_data.get('appbegin')
        append = cleaned_data.get('append')
        if appbegin is not None and append is not None:
            if append <= appbegin:
                raise ValidationError('Время окончания приема должно быть больше времени начала!', code='invalid')


class ProfileForm(forms.ModelForm):
    family = forms.CharField(required=False, disabled=True, label='Фамилия')
    name = forms.CharField(required=False, disabled=True, label='Имя')

    class Meta:
        model = Profile
        fields = ('family', 'name', 'patronymic', 'birth_date', 'gender', 'idnumber', 'fn')
        widgets = {
            'birth_date': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control datetimepicker-input',
                                                                    'type': 'date'})
        }


class BookingForm(forms.ModelForm):
    person = forms.ModelChoiceField(
        queryset=User.objects.filter(is_staff=False),
        label='Посетитель',
        widget=autocomplete.ModelSelect2(url='select2_fk_person')
    )

    class Meta:
        model = Booking
        fields = ('slot', 'person')

    def clean(self):
        super().clean()
        if Booking.objects.get(pk=self.instance.pk).person is not None:
            raise ValidationError('Выбранное время уже занято! Попробуйте другое.', code='invalid')

