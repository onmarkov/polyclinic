from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('appointment/', views.AppointmentListView.as_view(), name='appointment'),
    path('booking/appointment/<int:pk>/', views.BookingListView.as_view(), name='booking'),
    path('booking/update/', views.BookingUserUpdate.as_view(), name='booking_user'),
    path('booking/mybooking/', views.MyBookingListView.as_view(), name='mybooking'),
    path('person-autocomplete/', views.PersonAutocomplete.as_view(), name='select2_fk_person'),
    path('doctor-autocomplete/', views.DoctorAutocomplete.as_view(), name='select2_fk_doctor')
]
