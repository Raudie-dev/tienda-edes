from django.shortcuts import render, redirect
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
from app1.models import Product


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
        # Render login template directly to avoid redirect loops from repeated requests
        return render(request, 'login.html')
    try:
        user = User_admin.objects.get(id=user_id)
    except User_admin.DoesNotExist:
        messages.error(request, 'Usuario no encontrado')
        # Render login template directly to avoid redirect loops
        return render(request, 'login.html')

    # Nuevas operaciones: categorías y productos
    if request.method == 'POST':
        # Crear categoría
        if 'crear_categoria' in request.POST:
            nombre_cat = request.POST.get('categoria_nombre', '').strip()
            if nombre_cat:
                crear_categoria(nombre_cat)
                messages.success(request, 'Categoría creada')
            else:
                messages.error(request, 'El nombre de la categoría es obligatorio')

        # Crear producto
        elif 'crear_producto' in request.POST:
            nombre = request.POST.get('nombre', '').strip()
            precio = request.POST.get('precio', '0')
            descripcion = request.POST.get('descripcion', '')
            # aceptar múltiples categorias
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

        # Eliminar producto
        elif 'eliminar_producto' in request.POST:
            pid = request.POST.get('eliminar_producto')
            if pid:
                eliminar_producto(pid)
                messages.success(request, 'Producto eliminado')

        # Eliminar categoría
        elif 'eliminar_categoria' in request.POST:
            cid = request.POST.get('eliminar_categoria')
            if cid:
                eliminar_categoria(cid)
                messages.success(request, 'Categoría eliminada')

    # Después de cualquier POST redirigimos al control para evitar repost
    if request.method == 'POST':
        return redirect(reverse('registro'))

    categorias = obtener_categorias()
    productos = obtener_productos()
    return render(request, 'registro.html', {
        'productos': productos,
        'categorias': categorias,
    })


def control_productos(request):
    # Similar auth check
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
        # Edit product
        if 'editar_producto' in request.POST:
            pid = request.POST.get('editar_producto_id')
            if pid:
                nombre = request.POST.get('nombre', '').strip()
                precio = request.POST.get('precio', '0')
                descripcion = request.POST.get('descripcion', '')
                categoria_ids = request.POST.getlist('categoria_ids') or []
                imagen = request.FILES.get('imagen')
                agotado = True if request.POST.get('agotado') == 'on' else False
                try:
                    actualizar_producto(pid, nombre=nombre, precio=precio, descripcion=descripcion, categoria_ids=categoria_ids, imagen=imagen, agotado=agotado)
                    messages.success(request, 'Producto actualizado')
                except Exception as e:
                    messages.error(request, f'Error al actualizar producto: {e}')

        # Toggle agotado
        elif 'toggle_agotado' in request.POST:
            pid = request.POST.get('toggle_agotado')
            try:
                p = Product.objects.get(id=pid)
                p.agotado = not p.agotado
                p.save()
                messages.success(request, 'Estado actualizado')
            except Product.DoesNotExist:
                messages.error(request, 'Producto no encontrado')

        # Delete product
        elif 'eliminar_producto' in request.POST:
            pid = request.POST.get('eliminar_producto')
            if pid:
                eliminar_producto(pid)
                messages.success(request, 'Producto eliminado')

        return redirect(reverse('control_productos'))

    categorias = obtener_categorias()
    productos = obtener_productos()

    # --- filtros de búsqueda (GET) ---
    q = request.GET.get('q', '').strip()
    categoria_id = request.GET.get('categoria', '').strip()
    agotado_filter = request.GET.get('agotado', '').strip()  # values: '' or '1' (agotado) or '0' (disponible) or 'all'

    if q:
        productos = productos.filter(Q(nombre__icontains=q) | Q(descripcion__icontains=q))
    if categoria_id:
        try:
            cid = int(categoria_id)
            productos = productos.filter(categorias__id=cid)
        except ValueError:
            pass
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