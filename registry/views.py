from django.contrib.auth.models import User
from django.contrib.auth.decorators import permission_required
from django.db import IntegrityError
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, UpdateView
from django_tables2.views import SingleTableMixin
from django_filters.views import FilterView
from dal import autocomplete
from .tables import AppointmentTable, BookingTable, MyBookingTable
from .filters import AppointmentFilter
from .models import Appointment, Booking
from datetime import date


class HomeView(TemplateView):
    template_name = 'index.html'
    extra_context = {'title': 'Поликлиника'}


class AppointmentListView(SingleTableMixin, FilterView):
    table_class = AppointmentTable
    filterset_class = AppointmentFilter
    template_name = 'appointmentview.html'
    extra_context = {'title': 'Расписание приема врачей поликлиники',
                     'message': 'Возможность забронировать посещение в удобное время при наличии свободных талонов'}

    def dispatch(self, *args, **kwargs):
        self.request.session['back_for_booking'] = self.request.get_full_path()
        return super().dispatch(*args, **kwargs)

    def get_queryset(self, **kwargs):
        return Appointment.objects.filter(is_slots=True, dapp__gte=date.today())


class BookingListView(SingleTableMixin, ListView):
    table_class = BookingTable
    template_name = 'booking.html'
    extra_context = {'title': 'Бронирование посещения'}

    @method_decorator(permission_required('registry.view_booking', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_queryset(self, **kwargs):
        return Booking.objects.filter(appointment=self.kwargs['pk'], person__isnull=True).exclude(slot__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'back_for_booking' not in self.request.session or not self.request.session['back_for_booking']:
            self.request.session['back_for_booking'] = self.request.META.get('HTTP_REFERER', '/')
        context['previous_url'] = self.request.session['back_for_booking']
        context['message'] = Appointment.objects.get(pk=self.kwargs['pk'])
        return context


class MyBookingListView(SingleTableMixin, ListView):
    table_class = MyBookingTable
    template_name = 'appointmentview.html'
    extra_context = {'title': 'Мои бронирования посещений'}

    @method_decorator(permission_required('registry.view_booking', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_queryset(self, **kwargs):
        return Booking.objects.filter(person=self.request.user)


class BookingUserUpdate(UpdateView):

    @method_decorator(permission_required('registry.change_booking', raise_exception=True))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return get_object_or_404(Booking.objects.select_for_update(), pk=self.request.POST.getlist('reserve')[0])

    def post(self, request, *args, **kwargs):
        if request.POST.get('action') == 'done':
            self.object = self.get_object()
            if self.object.person is None:
                self.object.person = self.request.user
                try:
                    self.object.save()
                except IntegrityError:
                    mess = 'Невозможно провести бронирование! Возможно, что такой талон у Вас уже есть.'
                else:
                    mess = (
                        f'{self.object.person.first_name} {self.object.person.profile.patronymic}! '
                        f'{self.object} забронирован для посещения на время {self.object.slot:%H:%M}.'
                    )
                finally:
                    return render(request, 'booking_info.html', {'mess': mess, 'back': self.get_success_url()})
            else:
                mess = 'Время, выбранное Вами уже занято! Попробуйте другое.'
                return render(request, 'booking_info.html', {'mess': mess, 'back': self.get_success_url()})
        else:
            return redirect(self.get_success_url())

    def get_success_url(self):
        if 'back_for_booking' not in self.request.session or not self.request.session['back_for_booking']:
            return reverse_lazy('appointment')
        return self.request.session['back_for_booking']


class PersonAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return User.objects.none()
        qs = User.objects.filter(is_staff=False, is_active=True, groups__name='Посетители').\
            exclude(first_name='').exclude(last_name='').exclude(profile__birth_date__isnull=True).\
            order_by('last_name', 'first_name')
        if self.q:
            qs = qs.filter(last_name__istartswith=self.q)
        return qs

    def get_result_label(self, result):
        return f'{result.last_name} {result.first_name} {result.profile.patronymic} ({result.profile.birth_date:%d.%m.%Y})'


class DoctorAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return User.objects.none()
        qs = User.objects.filter(is_staff=False, is_active=True, groups__name='Врачи').\
            exclude(first_name='').exclude(last_name='').\
            order_by('last_name', 'first_name')
        if self.q:
            qs = qs.filter(last_name__istartswith=self.q)
        return qs

    def get_result_label(self, result):
        return f'{result.last_name} {result.first_name} {result.profile.patronymic}'
