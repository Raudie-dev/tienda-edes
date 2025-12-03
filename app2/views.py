from django.shortcuts import render, redirect, get_object_or_404
from urllib.parse import quote
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.db.models import Q
from .models import User_admin
from .crud import (
    crear_categoria,
    obtener_categorias,
    crear_producto,
    obtener_productos,
    eliminar_producto,
    eliminar_categoria,
    actualizar_producto,
)
from app1.models import Product, Cotizacion, CotizacionItem, Cliente


def login(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        password = request.POST.get('password', '')

        try:
            user = User_admin.objects.get(nombre=nombre)
            if user.bloqueado:
                messages.error(request, 'Usuario bloqueado')
            elif user.password == password or check_password(password, user.password):
                request.session['user_admin_id'] = user.id
                return redirect('registro')
            else:
                messages.error(request, 'Contraseña incorrecta')
            return render(request, 'login.html')
        except User_admin.DoesNotExist:
            messages.error(request, 'Usuario no encontrado')
            return render(request, 'login.html')

    return render(request, 'login.html')


def registro(request):
    user_id = request.session.get('user_admin_id')
    if not user_id:
        messages.error(request, 'Debe iniciar sesión primero')
        return render(request, 'login.html')
    
    try:
        user = User_admin.objects.get(id=user_id)
    except User_admin.DoesNotExist:
        messages.error(request, 'Usuario no encontrado')
        return render(request, 'login.html')

    # --- PROCESAMIENTO DE FORMULARIOS (POST) ---
    if request.method == 'POST':
        
        # 1. CREAR CATEGORÍA (Con soporte jerárquico)
        if 'crear_categoria' in request.POST:
            nombre_cat = request.POST.get('categoria_nombre', '').strip()
            
            # Capturamos el ID del padre del select
            padre_id = request.POST.get('categoria_padre')
            
            # Si el valor es vacío o string vacía, lo forzamos a None (Raíz)
            if not padre_id:
                padre_id = None
            
            if nombre_cat:
                try:
                    # Llamamos a la función corregida enviando el padre_id
                    crear_categoria(nombre_cat, padre_id)
                    messages.success(request, 'Categoría creada correctamente')
                except Exception as e:
                    messages.error(request, f'Error al crear la categoría: {e}')
            else:
                messages.error(request, 'El nombre de la categoría es obligatorio')

        # 2. CREAR PRODUCTO
        elif 'crear_producto' in request.POST:
            nombre = request.POST.get('nombre', '').strip()
            precio = request.POST.get('precio', '0')
            descripcion = request.POST.get('descripcion', '')
            
            # getlist obtiene todos los IDs seleccionados (Ctrl + Click)
            categoria_ids = request.POST.getlist('categoria_ids') or None
            
            imagen = request.FILES.get('imagen')
            
            if nombre:
                try:
                    crear_producto(nombre, precio, descripcion, categoria_ids, imagen)
                    messages.success(request, 'Producto creado correctamente')
                except Exception as e:
                    messages.error(request, f'Error al crear el producto: {e}')
            else:
                messages.error(request, 'El nombre del producto es obligatorio')

        # 3. ELIMINAR PRODUCTO
        elif 'eliminar_producto' in request.POST:
            pid = request.POST.get('eliminar_producto')
            if pid:
                eliminar_producto(pid)
                messages.success(request, 'Producto eliminado')

        # 4. ELIMINAR CATEGORÍA
        elif 'eliminar_categoria' in request.POST:
            cid = request.POST.get('eliminar_categoria')
            if cid:
                eliminar_categoria(cid)
                messages.success(request, 'Categoría eliminada')

        # Patrón PRG (Post-Redirect-Get) para evitar reenvíos al refrescar
        return redirect(reverse('registro'))

    # --- MÉTODO GET (Renderizar página) ---
    
    # Asegúrate que 'obtener_categorias()' devuelva el queryset correctamente.
    # Si quieres optimizar la carga del árbol jerárquico (N+1 problem):
    # categorias = Category.objects.prefetch_related('subcategorias__subcategorias').all()
    categorias = obtener_categorias()
    productos = obtener_productos()
    
    return render(request, 'registro.html', {
        'productos': productos,
        'categorias': categorias,
    })

def control_productos(request):
    user_id = request.session.get('user_admin_id')
    if not user_id:
        messages.error(request, 'Debe iniciar sesión primero')
        return redirect('login')

    try:
        user = User_admin.objects.get(id=user_id)
    except User_admin.DoesNotExist:
        messages.error(request, 'Usuario no encontrado')
        return redirect('login')

    if request.method == 'POST':
        
        # --- BLOQUE DE EDICIÓN CORREGIDO ---
        if 'editar_producto' in request.POST:
            producto_id = request.POST.get('editar_producto_id')
            
            try:
                # 1. Obtener el producto existente
                producto = Product.objects.get(id=producto_id)

                # 2. Asignar los nuevos valores desde el formulario
                producto.nombre = request.POST.get('nombre', '').strip()
                producto.descripcion = request.POST.get('descripcion', '')
                
                # 3. Convertir el precio a número
                try:
                    producto.precio = float(request.POST.get('precio', '0'))
                except (ValueError, TypeError):
                    messages.error(request, 'El precio ingresado no es un número válido.')
                    return redirect(reverse('control_productos'))

                # 4. Manejar el checkbox 'agotado'
                producto.agotado = 'agotado' in request.POST

                # 5. Manejar la imagen (solo si se sube una nueva)
                if 'imagen' in request.FILES:
                    producto.imagen = request.FILES['imagen']
                
                # 6. Guardar el objeto principal
                producto.save()

                # 7. Actualizar las categorías (ManyToMany)
                categoria_ids = request.POST.getlist('categoria_ids')
                producto.categorias.set(categoria_ids) # .set() es la forma correcta de actualizar un M2M

                messages.success(request, f'Producto "{producto.nombre}" actualizado correctamente.')

            except Product.DoesNotExist:
                messages.error(request, 'El producto que intentas editar no existe.')
            except Exception as e:
                messages.error(request, f'Ocurrió un error inesperado al actualizar: {e}')

        # Toggle agotado (Tu código aquí ya es correcto)
        elif 'toggle_agotado' in request.POST:
            pid = request.POST.get('toggle_agotado')
            producto = get_object_or_404(Product, id=pid)
            producto.agotado = not producto.agotado
            producto.save()
            messages.success(request, f'Estado de "{producto.nombre}" actualizado.')

        # Delete product (Tu código aquí parece correcto, asumiendo que eliminar_producto funciona)
        elif 'eliminar_producto' in request.POST:
            pid = request.POST.get('eliminar_producto')
            try:
                producto = Product.objects.get(id=pid)
                nombre_producto = producto.nombre
                producto.delete()
                messages.success(request, f'Producto "{nombre_producto}" eliminado.')
            except Product.DoesNotExist:
                 messages.error(request, 'Producto no encontrado.')

        # Siempre redirigir después de un POST exitoso
        return redirect(reverse('control_productos'))

    # --- Lógica GET para mostrar la página y filtros ---
    # Tu código para el método GET es correcto y no necesita cambios.
    categorias = obtener_categorias() # Asumo que esta función existe
    productos = obtener_productos() # Asumo que esta función existe

    q = request.GET.get('q', '').strip()
    categoria_id = request.GET.get('categoria', '').strip()
    agotado_filter = request.GET.get('agotado', '').strip()

    if q:
        productos = productos.filter(Q(nombre__icontains=q) | Q(descripcion__icontains=q))
    if categoria_id:
        productos = productos.filter(categorias__id=categoria_id)
    if agotado_filter == '1':
        productos = productos.filter(agotado=True)
    elif agotado_filter == '0':
        productos = productos.filter(agotado=False)

    productos = productos.distinct().order_by('-creado')

    return render(request, 'control_productos.html', {
        'productos': productos,
        'categorias': categorias,
        'q': q,
        'categoria_id': categoria_id,
        'agotado_filter': agotado_filter,
    })
    
# Nueva vista: listar solicitudes de cotización
def solicitudes_cotizacion(request):
    # --- 1. Autenticación (Código original) ---
    user_id = request.session.get('user_admin_id')
    if not user_id:
        messages.error(request, 'Debe iniciar sesión primero')
        return redirect('login')

    try:
        User_admin.objects.get(id=user_id)
    except Exception:
        messages.error(request, 'Usuario no encontrado')
        return redirect('login')

    # --- 2. QuerySet Base ---
    # Obtenemos la consulta base optimizada
    cotizaciones_qs = Cotizacion.objects.select_related('cliente').prefetch_related('items__producto').all().order_by('-creado')

    # --- 3. Lógica de Filtros ---
    
    # A) Filtro de Texto (Buscador)
    query = request.GET.get('q')
    if query:
        cotizaciones_qs = cotizaciones_qs.filter(
            Q(cliente__nombre__icontains=query) |   # Busca en nombre cliente
            Q(cliente__correo__icontains=query) |   # Busca en correo
            Q(cliente__telefono__icontains=query) | # Busca en teléfono (si existe el campo)
            Q(id__icontains=query)                  # Busca por ID de cotización
        )

    # B) Filtro de Estado
    estado = request.GET.get('estado')
    if estado:
        # Usamos iexact para ignorar mayúsculas/minúsculas (ej: 'Pendiente' == 'pendiente')
        cotizaciones_qs = cotizaciones_qs.filter(estado__iexact=estado)

    # --- 4. Procesamiento de Datos (Cálculo de Totales) ---
    solicitudes = []
    
    # Iteramos solo sobre las cotizaciones que pasaron los filtros
    for c in cotizaciones_qs:
        items = list(c.items.all())
        subtotal = 0.0
        
        for it in items:
            # Lógica original de precios: usar precio_unitario si está, si no usar precio del producto
            try:
                if it.precio_unitario not in (None, ''):
                    precio = float(it.precio_unitario)
                else:
                    precio = float(it.producto.precio or 0)
                
                cantidad = int(it.cantidad or 0)
                subtotal += precio * cantidad
            except ValueError:
                # Evita que la vista se rompa si hay datos corruptos en precio/cantidad
                pass 

        solicitudes.append({
            'cotizacion': c,
            'items': items,
            'subtotal': subtotal,
        })

    # --- 5. Renderizado ---
    context = {
        'solicitudes': solicitudes,
        'SHOW_PRICES': True, # Variable para controlar si se ven columnas de precios en el HTML
    }

    return render(request, 'solicitudes_cotizacion.html', context)

def procesar_y_responder_whatsapp(request, cotizacion_id):
    # 1. Verificar autenticación (igual que tus otras vistas)
    user_id = request.session.get('user_admin_id')
    if not user_id:
        messages.error(request, 'Debe iniciar sesión primero')
        return redirect('login')

    # 2. Obtener la cotización
    cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id)
    
    # 3. Actualizar estado a 'procesado' (si no está finalizado/aprobado)
    # Puedes ajustar esta condición según tu lógica de negocio
    if cotizacion.estado.lower() == 'pendiente':
        cotizacion.estado = 'procesado'
        cotizacion.save()
        messages.success(request, f"Cotización #{cotizacion.id} marcada como PROCESADA.")

    # 4. Construir el mensaje para WhatsApp (Lógica migrada del HTML a Python)
    items = cotizacion.items.all() # Asegúrate de que el related_name sea 'items'
    
    # Construcción del texto
    saludo = f"Saludos cordiales {cotizacion.cliente.nombre}, le escribimos desde EDES con respecto a su cotización de:\n"
    
    lista_productos = ""
    subtotal_general = 0.0

    for item in items:
        # Lógica de precio: Prioridad precio_unitario, sino precio producto
        precio = float(item.precio_unitario) if item.precio_unitario else float(item.producto.precio)
        cantidad = int(item.cantidad)
        total_item = precio * cantidad
        subtotal_general += total_item
        
        # Agregar línea al mensaje
        lista_productos += f"- {item.producto.nombre} (x{cantidad}): ${precio:.2f}\n"
    
    cierre = f"\nTotal Estimado: ${subtotal_general:.2f}"
    
    mensaje_completo = saludo + lista_productos + cierre
    
    # 5. Codificar mensaje para URL (convierte espacios en %20, etc.)
    mensaje_encoded = quote(mensaje_completo)
    
    # 6. Limpiar teléfono (quitar espacios, guiones o +)
    if cotizacion.cliente.telefono:
        telefono = cotizacion.cliente.telefono.replace(' ', '').replace('+', '').replace('-', '')
    else:
        telefono = "" # O manejar error si no tiene teléfono
    
    # 7. Redirigir a WhatsApp
    whatsapp_url = f"https://wa.me/{telefono}?text={mensaje_encoded}"
    
    return redirect(whatsapp_url)