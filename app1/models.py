from django.db import models

class Category(models.Model):
    nombre = models.CharField(max_length=120, unique=True)
    
    # --- CAMPO NUEVO PARA SUBCATEGORÍAS ---
    # 'self' indica relación con este mismo modelo.
    # null=True y blank=True permite que sea una categoría principal (sin padre).
    # related_name='subcategorias' es vital para el HTML que te pasé antes.
    padre = models.ForeignKey(
        'self', 
        null=True, 
        blank=True, 
        related_name='subcategorias', 
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'

    def __str__(self):
        # Si tiene padre, muestra "Padre > Hijo", si no, solo el nombre.
        if self.padre:
            return f"{self.padre.nombre} > {self.nombre}"
        return self.nombre


class Product(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # Permite múltiples categorías por producto
    categorias = models.ManyToManyField(Category, blank=True, related_name='productos')
    imagen = models.ImageField(upload_to='productos/', null=True, blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    agotado = models.BooleanField(default=False)

    def __str__(self):
        return self.nombre


class Cliente(models.Model):
    nombre = models.CharField(max_length=200)
    correo = models.EmailField()
    telefono = models.CharField(max_length=40, blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    def __str__(self):
        return f"{self.nombre} <{self.correo}>"


class Cotizacion(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='cotizaciones')
    mensaje = models.TextField(blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=30, default='pendiente')  # pendiente, procesado, finalizado, etc.

    class Meta:
        verbose_name = 'Cotización'
        verbose_name_plural = 'Cotizaciones'
        ordering = ['-creado']

    def __str__(self):
        return f"Cotización #{self.id} - {self.cliente.nombre}"


class CotizacionItem(models.Model):
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Product, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} (cot #{self.cotizacion_id})"