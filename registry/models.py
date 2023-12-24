import datetime
from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.dispatch import receiver


class Specialization(models.Model):
    id = models.BigAutoField(primary_key=True)
    specname = models.CharField(unique=True, max_length=30, verbose_name='Специализация')

    class Meta:
        managed = True
        db_table = 'specialization'
        verbose_name_plural = 'Справочник специализаций'
        verbose_name = 'Специализация'
        ordering = ['specname']

    def __str__(self):
        return self.specname


class Appointment(models.Model):
    HOUR_CHOICES = [(datetime.time(hour=x), '{:02d}:00'.format(x)) for x in range(7, 22)]
    id = models.BigAutoField(primary_key=True)
    dapp = models.DateField(verbose_name='День приема')
    specname = models.ForeignKey(Specialization, models.DO_NOTHING, verbose_name='Специализация')
    doctor = models.ForeignKey(User, models.DO_NOTHING, verbose_name='Врач')
    room = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)], verbose_name='Кабинет')
    appbegin = models.TimeField(choices=HOUR_CHOICES, verbose_name='Начало')
    append = models.TimeField(choices=HOUR_CHOICES, verbose_name='Окончание')
    planbudget = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)], verbose_name='Бюджет')
    plancommerce = models.PositiveSmallIntegerField(verbose_name='Внебюджет')
    is_slots = models.BooleanField(default=False, verbose_name='Талоны')

    class Meta:
        managed = True
        db_table = 'appointment'
        verbose_name_plural = 'Расписание приема'
        verbose_name = 'Строка расписания'
        unique_together = ('dapp', 'specname', 'doctor')
        index_together = ('dapp', 'specname', 'doctor')
        ordering = ('-dapp', 'specname', 'doctor')

    def doctor_fio(self):
        fio = f'{self.doctor.last_name} {self.doctor.first_name[0]}.'
        if self.doctor.profile.patronymic != '-':
            fio += f'{self.doctor.profile.patronymic[0]}.'
        return fio

    def btckt(self):
        return Booking.objects.filter(appointment=self.pk, slot__isnull=False, person__isnull=True).count()

    def ctckt(self):
        return Booking.objects.filter(appointment=self.pk, slot__isnull=True, person__isnull=True).count()

    def __str__(self):
        return f'Прием врача: {self.dapp:%d.%m.%Y}, {self.specname}, {self.doctor_fio()}'


class Booking(models.Model):
    id = models.BigAutoField(primary_key=True)
    appointment = models.ForeignKey(Appointment, models.DO_NOTHING, verbose_name='Расписание')
    slot = models.TimeField(null=True, blank=True, verbose_name='Время')
    person = models.ForeignKey(User, models.DO_NOTHING, null=True, blank=True, verbose_name='Посетитель')

    class Meta:
        managed = True
        db_table = 'booking'
        verbose_name_plural = 'Бронирование'
        verbose_name = 'Талон'
        index_together = ('appointment', 'slot')
        ordering = ('appointment', 'slot')
        constraints = [
            models.UniqueConstraint(fields=['appointment', 'person'], condition=models.Q(person__isnull=False),
                                    name='unique_appointment_person_person_is_not_null')
        ]

    def __str__(self):
        fio = f'{self.appointment.doctor.last_name} {self.appointment.doctor.first_name[0]}.'
        if self.appointment.doctor.profile.patronymic != '-':
            fio += f'{self.appointment.doctor.profile.patronymic[0]}.'
        mess = (
            f'Талон {self.appointment.dapp:%d.%m.%Y}, {self.appointment.specname}, '
            f'{fio}, к.{self.appointment.room} '
            f'({self.appointment.appbegin:%H:%M}-{self.appointment.append:%H:%M})'
        )
        return mess


class Profile(models.Model):
    GENDER_CHOICES = [('Ж', 'Женский'), ('М', 'Мужской')]
    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Посетитель')
    birth_date = models.DateField(null=True, blank=True, verbose_name='Дата рождения')
    gender = models.CharField(choices=GENDER_CHOICES, max_length=1, blank=True, null=True, verbose_name='Пол')
    patronymic = models.CharField(max_length=30, default='-', null=True, verbose_name='Отчество')
    idnumber = models.CharField(unique=True, max_length=11, null=True, blank=True, verbose_name='Номер документа')
    fn = models.CharField(max_length=200, blank=True, null=True, verbose_name='Примечание')

    class Meta:
        app_label = 'auth'
        managed = True
        db_table = 'auth_profile'
        verbose_name_plural = 'Пользователи (дополнение)'
        verbose_name = 'Пользователь (сотрудник, посетитель)'

    def __str__(self):
        return f'{self.user.last_name} {self.user.first_name} {self.patronymic} ({self.user})'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
