from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from .models import Category, Product
from . import crud
import random
from django.conf import settings  # Importar settings para usar las variables
from django.core.mail import EmailMultiAlternatives # Para enviar HTML
from django.template.loader import render_to_string # Para renderizar el HTML
from django.utils.html import strip_tags # Para limpiar HTML para la versión texto plano
from django.core.mail import send_mail

def _get_cart_count(request):
    cart = request.session.get('cotizacion', {}) or {}
    try:
        return sum(int(v) for v in cart.values())
    except Exception:
        return 0

# Vista de inicio mejorada con 4 productos aleatorios
def index(request):
    categoria_id = request.GET.get('categoria')
    categorias = Category.objects.all()
    
    # 1. Obtenemos todos los productos (Recomendación: Solo los no agotados)
    # Si quieres mostrar agotados también, usa Product.objects.all()
    productos = Product.objects.filter(agotado=False) 

    # 2. Aplicamos el filtro de categoría si existe
    if categoria_id:
        try:
            productos = productos.filter(categorias__id=int(categoria_id))
        except (ValueError, TypeError):
            pass

    # 3. AQUÍ APLICAMOS LA LÓGICA DE "4 ALEATORIOS"
    # .order_by('?') -> Mezcla los resultados aleatoriamente
    # [:4] -> Corta la lista y se queda solo con los primeros 4
    productos = productos.order_by('?')[:4]

    cart_count = _get_cart_count(request)
    
    return render(request, 'index.html', {
        'categorias': categorias,
        'productos': productos, # Ahora esta variable solo lleva 4 items aleatorios
        'categoria_id': categoria_id,
        'cart_count': cart_count,
    })

# Nueva vista: tienda pública con búsqueda y filtros
def tienda(request):
    # Optimización: Cargar subcategorías de una vez para el menú
    categorias = Category.objects.prefetch_related('subcategorias').all()
    
    # Base de productos
    productos = Product.objects.prefetch_related('categorias').all()

    q = request.GET.get('q', '').strip()
    categoria_id = request.GET.get('categoria', '').strip()
    agotado_filter = request.GET.get('agotado', '').strip()  # '' | '1' | '0'

    # 1. Filtro por Texto
    if q:
        from django.db.models import Q
        productos = productos.filter(Q(nombre__icontains=q) | Q(descripcion__icontains=q))

    # 2. Filtro por Categoría (MEJORADO PARA SUBCATEGORÍAS)
    if categoria_id:
        try:
            cid = int(categoria_id)
            # Buscamos la categoría seleccionada
            cat_obj = Category.objects.get(id=cid)
            
            # Obtenemos una lista con el ID seleccionado + IDs de sus hijos
            # values_list('id', flat=True) devuelve solo los números [1, 5, 8...]
            ids_a_buscar = list(cat_obj.subcategorias.values_list('id', flat=True))
            ids_a_buscar.append(cid) # Agregamos el padre también
            
            # Filtramos productos que estén en CUALQUIERA de esos IDs
            productos = productos.filter(categorias__id__in=ids_a_buscar)
            
        except (ValueError, TypeError, Category.DoesNotExist):
            pass # Si el ID no es válido o no existe, ignoramos el filtro

    # 3. Filtro por Disponibilidad
    if agotado_filter == '1':
        productos = productos.filter(agotado=True)
    elif agotado_filter == '0':
        productos = productos.filter(agotado=False)

    productos = productos.distinct().order_by('-creado')
    
    # Asumo que esta función auxiliar la tienes definida en tu archivo
    cart_count = _get_cart_count(request)

    return render(request, 'tienda.html', {
        'categorias': categorias,
        'productos': productos,
        'q': q,
        'categoria_id': categoria_id,
        'agotado_filter': agotado_filter,
        'cart_count': cart_count,
    })


# Vista de detalle de producto
def productos(request, producto_id):
    producto = get_object_or_404(Product, id=producto_id)
    imagenes = [producto.imagen] if producto.imagen else []

    sugeridos = Product.objects.exclude(id=producto.id)
    first_cat = producto.categorias.first()
    if first_cat:
        sugeridos = sugeridos.filter(categorias=first_cat)
    sugeridos = list(sugeridos)
    random.shuffle(sugeridos)
    sugeridos = sugeridos[:4]

    cart_count = _get_cart_count(request)
    return render(request, 'productos.html', {
        'producto': producto,
        'imagenes': imagenes,
        'sugeridos': sugeridos,
        'cart_count': cart_count,
    })

# Nueva vista: añadir item al carrito de cotización (session)
def cotizacion_add(request):
    if request.method != 'POST':
        return redirect(request.META.get('HTTP_REFERER', reverse('tienda')))
    prod_id = request.POST.get('product_id')
    try:
        qty = int(request.POST.get('cantidad', '1'))
        if qty < 1:
            qty = 1
    except (ValueError, TypeError):
        qty = 1
    if not prod_id:
        messages.error(request, 'Producto inválido')
        return redirect(request.META.get('HTTP_REFERER', reverse('tienda')))

    cart = request.session.get('cotizacion', {}) or {}
    cart = dict(cart)
    current = int(cart.get(str(prod_id), 0))
    current += qty
    cart[str(prod_id)] = current
    request.session['cotizacion'] = cart
    request.session.modified = True
    messages.success(request, 'Producto agregado a la solicitud de cotización')
    return redirect(request.META.get('HTTP_REFERER', reverse('tienda')))

# Nueva vista: mostrar carrito de cotización y enviar solicitud
def cotizacion(request):
    cart = request.session.get('cotizacion', {}) or {}
    product_ids = [int(k) for k in cart.keys() if k.isdigit()]
    productos = Product.objects.filter(id__in=product_ids)
    items = []
    subtotal = 0
    prod_map = {p.id: p for p in productos}
    
    # Reconstruimos los items
    for pid_str, qty in cart.items():
        try:
            pid = int(pid_str)
        except ValueError:
            continue
        prod = prod_map.get(pid)
        if not prod:
            continue
        cantidad = int(qty)
        total = prod.precio * cantidad
        items.append({'product': prod, 'cantidad': cantidad, 'total': total})
        subtotal += total

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        correo = request.POST.get('correo', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        mensaje = request.POST.get('mensaje', '').strip()

        if not nombre or not correo:
            messages.error(request, 'Nombre y correo son obligatorios para enviar la solicitud.')
            return render(request, 'cotizacion.html', {'items': items, 'subtotal': subtotal, 'cart_count': _get_cart_count(request)})

        try:
            # 1. Crear cliente y cotización en BD
            cliente = crud.crear_cliente(nombre, correo, telefono)
            items_payload = [{'product_id': p['product'].id, 'cantidad': p['cantidad']} for p in items]
            cot = crud.crear_cotizacion_desde_carrito(cliente, items_payload, mensaje=mensaje)
            
            # --- INICIO LÓGICA DE ENVÍO DE CORREO ---
            
            # Asunto del correo
            subject = f'Nueva Solicitud de Cotización - {nombre}'
            
            # Contexto para la plantilla del correo
            email_context = {
                'nombre': nombre,
                'correo': correo,
                'telefono': telefono,
                'mensaje': mensaje,
                'items': items,
                'subtotal': subtotal,
                'cotizacion_id': cot.id if cot else 'N/A'
            }

            # Renderizar el contenido HTML
            html_content = render_to_string('emails/cotizacion_email.html', email_context)
            # Crear versión de texto plano (buena práctica para evitar spam)
            text_content = strip_tags(html_content)

            # Configurar el correo
            msg = EmailMultiAlternatives(
                subject,                # Asunto
                text_content,           # Contenido texto plano
                settings.EMAIL_HOST_USER, # De: (edsnotificaciones@gmail.com)
                [settings.CORREO_VENTAS]  # Para: (ventas@edesvenezuela.com)
            )
            
            # Adjuntar el contenido HTML
            msg.attach_alternative(html_content, "text/html")
            
            # Enviar
            msg.send()
            
            # --- FIN LÓGICA DE ENVÍO DE CORREO ---

            # Limpiar carrito y finalizar
            request.session['cotizacion'] = {}
            request.session.modified = True
            return render(request, 'cotizacion_success.html', {'cotizacion': cot, 'cart_count': 0})
            
        except Exception as e:
            # Es útil imprimir el error en consola para depurar si falla el correo
            print(f"Error procesando cotización/correo: {e}") 
            messages.error(request, f'Error al crear la solicitud: {e}')
            return render(request, 'cotizacion.html', {'items': items, 'subtotal': subtotal, 'cart_count': _get_cart_count(request)})

    return render(request, 'cotizacion.html', {'items': items, 'subtotal': subtotal, 'cart_count': _get_cart_count(request)})


def guardar_contacto(request):
    if request.method == "POST":
        # 1. Obtener los datos del formulario (sin cambios)
        nombre = request.POST.get('nombre', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        correo = request.POST.get('correo', '').strip()
        motivo_form = request.POST.get('motivo')
        mensaje = request.POST.get('mensaje', '').strip()

        # 2. Traducir el motivo a un texto legible (sin cambios)
        motivos_map = {
            'cotizacion_repuestos': 'Solicitar Cotización de Repuestos',
            'soporte_tecnico': 'Soporte Técnico / Mantenimiento',
            'alquiler_equipos': 'Información sobre Alquiler de Equipos',
            'info_general': 'Consulta General',
            'otro': 'Otro',
        }
        motivo_legible = motivos_map.get(motivo_form, 'No especificado')

        # --- INICIO LÓGICA DE ENVÍO DE CORREO (AJUSTADA) ---
        
        try:
            # 3. Preparar el contexto para la plantilla del correo
            email_context = {
                'nombre': nombre,
                'telefono': telefono,
                'correo': correo,
                'motivo_legible': motivo_legible,
                'mensaje': mensaje,
            }

            # 4. Renderizar SÓLO la plantilla HTML
            html_content = render_to_string('emails/nuevo_contacto.html', email_context)
            # 5. Crear la versión de texto plano automáticamente desde el HTML
            text_content = strip_tags(html_content)

            # 6. Configurar el correo usando EmailMultiAlternatives
            subject = f'Nuevo Contacto desde la Web: {motivo_legible}'
            
            msg = EmailMultiAlternatives(
                subject,                       # Asunto
                text_content,                  # Contenido en texto plano (body)
                settings.EMAIL_HOST_USER,      # De: (tu correo de notificaciones)
                [settings.CORREO_VENTAS]       # Para: (el correo de ventas)
            )
            
            # 7. Adjuntar la versión HTML
            msg.attach_alternative(html_content, "text/html")
            
            # 8. Enviar el correo
            msg.send()

            # --- FIN LÓGICA DE ENVÍO DE CORREO ---
            
            # 9. Mostrar mensaje de éxito al usuario
            messages.success(request, '¡Gracias por contactarnos! Hemos recibido tu mensaje y te responderemos pronto.')
        
        except Exception as e:
            # En caso de error, es útil registrarlo para depuración
            print(f"Error al enviar correo de contacto: {e}")
            messages.error(request, 'Hubo un error al enviar tu mensaje. Por favor, inténtalo de nuevo o contáctanos directamente.')

        # 10. Redirigir de vuelta al formulario en la página de inicio
        return redirect('/#contacto')

    # Si alguien intenta acceder a la URL por método GET, redirigir al inicio
    return redirect('/')