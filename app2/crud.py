from django.core.exceptions import ObjectDoesNotExist
from app1.models import Product, Category


def crear_categoria(nombre, padre_id=None):
    """
    Crea una categoría nueva o devuelve la existente.
    Acepta un padre_id opcional para crear subcategorías.
    """
    nombre = (nombre or '').strip()
    if not nombre:
        return None
    
    # Preparamos los valores por defecto si se tiene que crear nueva
    defaults = {}
    if padre_id:
        defaults['padre_id'] = padre_id
        
    # get_or_create busca por nombre. Si no existe, usa 'defaults' para crearla con el padre.
    cat, created = Category.objects.get_or_create(
        nombre=nombre,
        defaults=defaults
    )
    return cat


def obtener_categorias():
    """
    Obtiene todas las categorías.
    Usamos 'prefetch_related' para cargar las subcategorías eficientemente
    y evitar lentitud en la plantilla HTML.
    """
    return Category.objects.prefetch_related('subcategorias').all()


def eliminar_categoria(cat_id):
    Category.objects.filter(id=cat_id).delete()


def crear_producto(nombre, precio, descripcion='', categoria_ids=None, imagen=None):
    """Crea un producto. `imagen` puede ser un File (request.FILES['imagen']).
    `categoria_ids` puede ser una lista de ids o None."""
    nombre = (nombre or '').strip()
    if not nombre:
        raise ValueError('El nombre es obligatorio')
    try:
        precio_val = float(precio)
    except (TypeError, ValueError):
        precio_val = 0

    producto = Product.objects.create(
        nombre=nombre,
        precio=precio_val,
        descripcion=descripcion or '',
        imagen=imagen,
    )

    # Asociar categorías si se entregaron ids
    if categoria_ids:
        # categoria_ids puede venir como lista de strings
        ids = [int(x) for x in categoria_ids if x]
        cats = Category.objects.filter(id__in=ids)
        producto.categorias.set(cats)

    return producto


def obtener_productos():
    # Prefetch M2M categorias para optimizar la carga
    return Product.objects.prefetch_related('categorias').all()


def eliminar_producto(producto_id):
    Product.objects.filter(id=producto_id).delete()


def actualizar_producto(producto_id, **kwargs):
    """Actualizar campos permitidos de un producto."""
    try:
        p = Product.objects.get(id=producto_id)
    except ObjectDoesNotExist:
        return None

    for field in ('nombre', 'descripcion', 'precio', 'agotado'):
        if field in kwargs and kwargs[field] is not None:
            setattr(p, field, kwargs[field])

    # Soporte para actualizar categorias (lista de ids)
    if 'categoria_ids' in kwargs:
        cat_ids = kwargs.get('categoria_ids') or []
        ids = [int(x) for x in cat_ids if x]
        cats = Category.objects.filter(id__in=ids)
        p.categorias.set(cats)

    if 'imagen' in kwargs and kwargs['imagen'] is not None:
        p.imagen = kwargs['imagen']

    p.save()
    return p