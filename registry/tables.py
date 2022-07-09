import django_tables2 as tables
from . models import Appointment, Booking


class AppointmentTable(tables.Table):
    doctor_fio = tables.Column(verbose_name='Врач')
    appbegin = tables.Column()
    append = tables.Column()
    btckt = tables.Column(verbose_name='Бюджет')
    ctckt = tables.Column(verbose_name='Внебюджет')
    actions = tables.TemplateColumn(verbose_name='', template_name='actionscolumn.html')

    class Meta:
        model = Appointment
        attrs = {'class': 'table table-hover table-condensed'}
        fields = ('dapp', 'specname', 'doctor_fio', 'room', 'appbegin', 'append', 'btckt', 'ctckt')


class BookingTable(tables.Table):
    reserve = tables.TemplateColumn('<input type="checkbox" name="reserve" value="{{ record.pk }}" />',
                                    verbose_name='Бронировать')

    class Meta:
        model = Booking
        fields = ('slot', 'reserve')

    def render_slot(self, value):
        if value:
            return value
        else:
            return 'Без очереди'


class MyBookingTable(tables.Table):
    appointment__doctor_fio = tables.Column(verbose_name='Врач')
    appointment__appbegin = tables.Column()
    appointment__append = tables.Column()

    class Meta:
        model = Booking
        attrs = {'class': 'table table-hover table-condensed'}
        fields = ('appointment__dapp', 'appointment__specname', 'appointment__doctor_fio', 'appointment__room',
                  'appointment__appbegin', 'appointment__append', 'slot')
