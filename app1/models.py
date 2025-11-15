from django.db import models


class Category(models.Model):
    nombre = models.CharField(max_length=120, unique=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'

    def __str__(self):
        return self.nombre


class Product(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # Allow multiple categories per product
    categorias = models.ManyToManyField(Category, blank=True, related_name='productos')
    imagen = models.ImageField(upload_to='productos/', null=True, blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    agotado = models.BooleanField(default=False)

    def __str__(self):
        return self.nombre