from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('producto/<int:producto_id>/', views.productos, name='productos'),
    path('tienda/', views.tienda, name='tienda'),
    # Cotización / carrito de solicitud
    path('cotizacion/', views.cotizacion, name='cotizacion'),
    path('cotizacion/add/', views.cotizacion_add, name='cotizacion_add'),
    path('guardar-contacto/', views.guardar_contacto, name='guardar_contacto'),
]