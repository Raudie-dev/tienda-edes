from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
urlpatterns = [
    path('login/', views.login, name='login'),
    path('registro/', views.registro, name='registro'),
    path('control_productos/', views.control_productos, name='control_productos'),
    path('solicitudes/', views.solicitudes_cotizacion, name='solicitudes_cotizacion'),
    path('cotizacion/responder/<int:cotizacion_id>/', views.procesar_y_responder_whatsapp, name='responder_whatsapp'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('usuarios/', views.gestion_usuarios, name='usuarios'), 
]