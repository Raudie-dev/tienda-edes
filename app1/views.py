from django.shortcuts import render
from .models import Category, Product

def index(request):
    categoria_id = request.GET.get('categoria')
    categorias = Category.objects.all()
    productos = Product.objects.all()
    if categoria_id:
        try:
            productos = productos.filter(categorias__id=int(categoria_id))
        except (ValueError, TypeError):
            pass
    return render(request, 'index.html', {
        'categorias': categorias,
        'productos': productos,
        'categoria_id': categoria_id,
    })

# Nueva vista: tienda pública con búsqueda y filtros
def tienda(request):
    categorias = Category.objects.all()
    productos = Product.objects.prefetch_related('categorias').all()

    q = request.GET.get('q', '').strip()
    categoria_id = request.GET.get('categoria', '').strip()
    agotado_filter = request.GET.get('agotado', '').strip()  # '' | '1' | '0'

    if q:
        from django.db.models import Q
        productos = productos.filter(Q(nombre__icontains=q) | Q(descripcion__icontains=q))
    if categoria_id:
        try:
            productos = productos.filter(categorias__id=int(categoria_id))
        except (ValueError, TypeError):
            pass
    if agotado_filter == '1':
        productos = productos.filter(agotado=True)
    elif agotado_filter == '0':
        productos = productos.filter(agotado=False)

    productos = productos.distinct().order_by('-creado')

    return render(request, 'tienda.html', {
        'categorias': categorias,
        'productos': productos,
        'q': q,
        'categoria_id': categoria_id,
        'agotado_filter': agotado_filter,
    })


# Vista de detalle de producto
from django.shortcuts import get_object_or_404
import random

def productos(request, producto_id):
    producto = get_object_or_404(Product, id=producto_id)
    # Carrusel: por ahora solo una imagen, pero estructura lista para varias
    imagenes = [producto.imagen] if producto.imagen else []

    # Sugeridos: otros productos de la misma (primera) categoría, si hay; si no, aleatorios
    sugeridos = Product.objects.exclude(id=producto.id)
    first_cat = producto.categorias.first()
    if first_cat:
        sugeridos = sugeridos.filter(categorias=first_cat)
    sugeridos = list(sugeridos)
    random.shuffle(sugeridos)
    sugeridos = sugeridos[:4]

    return render(request, 'productos.html', {
        'producto': producto,
        'imagenes': imagenes,
        'sugeridos': sugeridos,
    })
