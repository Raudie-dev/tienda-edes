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


from django.db import models

class Product(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # Permite múltiples categorías por producto
    categorias = models.ManyToManyField('Category', blank=True, related_name='productos') # Asegúrate que 'Category' coincida con tu modelo
    imagen = models.ImageField(upload_to='productos/', null=True, blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    agotado = models.BooleanField(default=False)

    def __str__(self):
        return self.nombre

    @property
    def categorias_hoja(self):
        """
        Retorna solo las categorías más específicas.
        Si el producto tiene 'Electrónica' y 'Electrónica -> Celulares',
        este método devuelve solo 'Celulares'.
        """
        # Obtenemos todas las categorías asignadas al producto
        todas = list(self.categorias.all())
        hojas = []

        for cat in todas:
            es_padre = False
            # Comparamos 'cat' contra todas las otras categorías 'otra'
            for otra in todas:
                if cat.id != otra.id:
                    # Verificamos si 'cat' es ancestro de 'otra'
                    # Recorremos hacia arriba desde 'otra'
                    padre_iter = otra.padre
                    while padre_iter:
                        if padre_iter.id == cat.id:
                            es_padre = True
                            break
                        padre_iter = padre_iter.padre
                if es_padre:
                    break
            
            # Si 'cat' NO es padre de ninguna otra categoría en la lista, es una hoja
            if not es_padre:
                hojas.append(cat)
        
        return hojas


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
    producto = models.ForeignKey(Product, on_delete=models.CASCADE)  # ← Cambiado aquí
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} (cot #{self.cotizacion_id})"
