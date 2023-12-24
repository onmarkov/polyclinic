import datetime
from django import forms
from django.contrib import admin, messages
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Specialization, Appointment, Profile, Booking
from .forms import AppointmentForm, ProfileForm, BookingForm


class SpecializationAdmin(admin.ModelAdmin):
    list_display = ['specname']
    search_fields = ['specname']

    def delete_view(self, request, object_id, extra_context=None):
        try:
            return super().delete_view(request, object_id, extra_context)
        except IntegrityError:
            msg = "Невозможно удалить родительский объект (Специализация), т.к. есть дочерние объекты, ссылающиеся на него"
            self.message_user(request, msg, messages.ERROR)
            opts = self.model._meta
            return_url = reverse('admin:%s_%s_change' % (opts.app_label, opts.model_name), args=(object_id,),
                                 current_app=self.admin_site.name, )
            return HttpResponseRedirect(return_url)

    def response_action(self, request, queryset):
        try:
            return super().response_action(request, queryset)
        except IntegrityError:
            msg = "Невозможно удалить родительский объект (Специализация), т.к. есть дочерние объекты, ссылающиеся на него"
            self.message_user(request, msg, messages.ERROR)
            opts = self.model._meta
            return_url = reverse('admin:%s_%s_changelist' % (opts.app_label, opts.model_name),
                                 current_app=self.admin_site.name, )
            return HttpResponseRedirect(return_url)


class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('dapp', 'specname', 'doctor_fio', 'room', 'appbegin', 'append', 'planbudget', 'plancommerce', 'is_slots')
    list_display_links = ['dapp']
    search_fields = ['doctor__last_name']
    list_filter = ('dapp', 'specname')
    date_hierarchy = 'dapp'
    fieldsets = [
        (None, {'fields': ['dapp', 'specname', 'doctor', 'room']}),
        ('Часы приема', {'fields': ['appbegin', 'append']}),
        ('План приема', {'fields': ['planbudget', 'plancommerce']})
    ]
    actions = ['create_slots', 'delete_slots']
    change_form_template = "registry_changeform.html"
    form = AppointmentForm

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            actions['delete_selected'][0].short_description = 'Удаление выбранных строк расписания'
        return actions

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['doctor'].label_from_instance = lambda obj: f'{obj.last_name} {obj.first_name} ' \
                                                                     f'{obj.profile.patronymic}'
        return form

    @staticmethod
    def time_slots(date, start_time, end_time, n):
        delta = (datetime.datetime.combine(date, end_time) - datetime.datetime.combine(date, start_time)) / n
        t = start_time
        while t < end_time:
            yield t.strftime('%H:%M')
            t = (datetime.datetime.combine(datetime.date.today(), t) + delta).time()

    def create_slots(self, request, queryset):
        for rec in queryset:
            if not rec.is_slots:
                for _ in range(rec.plancommerce):
                    Booking.objects.create(appointment_id=rec.id)
                if rec.planbudget > 0:
                    gen = self.time_slots(rec.dapp, rec.appbegin, rec.append, rec.planbudget)
                    for _ in range(rec.planbudget):
                        Booking.objects.create(appointment_id=rec.id, slot=next(gen))
                    gen.close()
                    del gen
                Appointment.objects.filter(pk=rec.id).update(is_slots=True)

    def delete_slots(self, request, queryset):
        self.message_user(request, "Внимание! Удаление возможно, если все талоны строки расписания свободны!", messages.INFO)
        for rec in queryset:
            if rec.is_slots:
                bt = Booking.objects.filter(appointment=rec.id).exclude(person=None).count()
                if bt == 0:
                    Booking.objects.filter(appointment=rec.id).delete()
                    Appointment.objects.filter(pk=rec.id).update(is_slots=False)

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        if obj and obj.is_slots:
            return readonly_fields + ('appbegin', 'append', 'planbudget', 'plancommerce')
        return readonly_fields

    def get_changeform_initial_data(self, request):
        return {'dapp': datetime.date.today()+datetime.timedelta(days=1), 'planbudget': 1, 'plancommerce': 0, 'is_slots': False}

    def delete_view(self, request, object_id, extra_context=None):
        try:
            return super().delete_view(request, object_id, extra_context)
        except IntegrityError:
            msg = "Невозможно удалить родительский объект (Расписание приема), т.к. есть дочерние объекты, ссылающиеся на него"
            self.message_user(request, msg, messages.ERROR)
            opts = self.model._meta
            return_url = reverse('admin:%s_%s_change' % (opts.app_label, opts.model_name), args=(object_id,),
                                 current_app=self.admin_site.name, )
            return HttpResponseRedirect(return_url)

    def response_action(self, request, queryset):
        try:
            return super().response_action(request, queryset)
        except IntegrityError:
            msg = "Невозможно удалить родительский объект (Расписание приема), т.к. есть дочерние объекты, ссылающиеся на него"
            self.message_user(request, msg, messages.ERROR)
            opts = self.model._meta
            return_url = reverse('admin:%s_%s_changelist' % (opts.app_label, opts.model_name),
                                 current_app=self.admin_site.name, )
            return HttpResponseRedirect(return_url)

    def doctor_fio(self, obj):
        return obj.doctor_fio()

    doctor_fio.short_description = 'Врач'
    create_slots.short_description = 'Создание талонов для бронирования'
    delete_slots.short_description = 'Удаление талонов для бронирования'


class BookingAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'slot', 'person', 'person_family', 'person_name', 'person_patronymic', 'person_birth_date')
    readonly_fields = ['slot']
    exclude = ['appointment']
    date_hierarchy = 'appointment__dapp'
    list_filter = ['appointment__specname']
    search_fields = ['person__last_name']
    actions = ['cancel_booking']
    change_form_template = "registry_changeform.html"
    form = BookingForm

    def has_add_permission(self, request):
        return False

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_save_and_continue'] = False
        extra_context['show_delete'] = False
        if Booking.objects.get(pk=object_id).person is not None:
            extra_context['show_save'] = False
        try:
            return super().change_view(request, object_id, form_url, extra_context=extra_context)
        except IntegrityError:
            msg = "Невозможно провести бронирование! Возможно, что такой талон уже есть."
            self.message_user(request, msg, messages.ERROR)
            opts = self.model._meta
            return_url = reverse('admin:%s_%s_change' % (opts.app_label, opts.model_name), args=(object_id,),
                                 current_app=self.admin_site.name, )
            return HttpResponseRedirect(return_url)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['person'].label_from_instance = lambda obj: f'{obj.last_name} {obj.first_name} ' \
                                                                     f'{obj.profile.patronymic} ' \
                                                                     f'({obj.profile.birth_date:%d.%m.%Y})'
        return form

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def cancel_booking(self, request, queryset):
        for rec in queryset:
            Booking.objects.filter(pk=rec.id).update(person=None)

    def person_family(self, obj):
        res = None
        if obj.person is not None:
            res = obj.person.last_name
        return res

    def person_name(self, obj):
        res = None
        if obj.person is not None:
            res = obj.person.first_name
        return res

    def person_patronymic(self, obj):
        res = None
        if obj.person is not None:
            res = obj.person.profile.patronymic
        return res

    def person_birth_date(self, obj):
        res = None
        if obj.person is not None:
            res = obj.person.profile.birth_date
        return res

    person_family.short_description = 'Фамилия'
    person_name.short_description = 'Имя'
    person_patronymic.short_description = 'Отчество'
    person_birth_date.short_description = 'Д.Р.'
    cancel_booking.short_description = 'Отмена бронирования'


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'patient_family', 'patient_name', 'patronymic', 'birth_date', 'gender', 'idnumber')
    search_fields = ('user__username', 'user__last_name')
    exclude = ['user']
    change_form_template = "registry_changeform.html"
    form = ProfileForm

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['family'].initial = self.patient_family(obj)
        form.base_fields['name'].initial = self.patient_name(obj)
        return form

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user').exclude(user__first_name='').exclude(user__last_name='')

    def formfield_for_dbfield(self, db_field, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'fn':
            formfield.widget = forms.Textarea(attrs={'cols': 80, 'rows': 10})
        return formfield

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        if isinstance(obj, Profile):
            opts = self.model._meta
            if request.path == reverse('admin:%s_%s_change' % (opts.app_label, opts.model_name), args=[obj.id]):
                return False
        return True

    def patient_family(self, obj):
        return obj.user.last_name

    def patient_name(self, obj):
        return obj.user.first_name

    patient_family.short_description = 'Фамилия'
    patient_name.short_description = 'Имя'


class CustomUserAdmin(UserAdmin):

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(is_staff=False)
        return qs

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        if not request.user.is_superuser:
            if obj:
                return readonly_fields + ('is_staff', 'is_superuser', 'user_permissions', 'last_login', 'date_joined')
        return readonly_fields

    def get_list_display(self, request):
        if not request.user.is_superuser:
            return ['username', 'first_name', 'last_name', 'is_active', 'get_groups']
        else:
            return super().get_list_display(request)

    def get_list_filter(self, request):
        if not request.user.is_superuser:
            return ['is_active', 'groups']
        else:
            return super().get_list_filter(request)

    @staticmethod
    @admin.display(description='Группа')
    def get_groups(obj):
        return ','.join([str(grpname) for grpname in obj.groups.values_list('name', flat=True)])

    def delete_view(self, request, object_id, extra_context=None):
        try:
            return super().delete_view(request, object_id, extra_context)
        except IntegrityError:
            msg = "Невозможно удалить родительский объект (Пользователь), т.к. есть дочерние объекты, ссылающиеся на него"
            self.message_user(request, msg, messages.ERROR)
            opts = self.model._meta
            return_url = reverse('admin:%s_%s_change' % (opts.app_label, opts.model_name), args=(object_id,),
                                 current_app=self.admin_site.name, )
            return HttpResponseRedirect(return_url)

    def response_action(self, request, queryset):
        try:
            return super().response_action(request, queryset)
        except IntegrityError:
            msg = "Невозможно удалить родительский объект (Пользователь), т.к. есть дочерние объекты, ссылающиеся на него"
            self.message_user(request, msg, messages.ERROR)
            opts = self.model._meta
            return_url = reverse('admin:%s_%s_changelist' % (opts.app_label, opts.model_name),
                                 current_app=self.admin_site.name, )
            return HttpResponseRedirect(return_url)


admin.site.site_header = 'Управление регистратурой'
admin.site.site_title = "Регистратура"
admin.site.index_title = 'Административный раздел'

admin.site.register(Specialization, SpecializationAdmin)
admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Booking, BookingAdmin)

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
