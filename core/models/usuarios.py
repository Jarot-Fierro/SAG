from django.contrib.auth.models import AbstractUser
from django.core.cache import cache
from django.db import models
from simple_history.models import HistoricalRecords

from config import settings


class User(AbstractUser):
    username = models.CharField(max_length=200, unique=True)
    password = models.CharField(max_length=128)
    establecimiento = models.ForeignKey('core.Establecimiento', on_delete=models.PROTECT, null=True,
                                        blank=True,
                                        verbose_name='Establecimiento'
                                        )
    departamento = models.ForeignKey('core.Departamento', on_delete=models.PROTECT, null=True,
                                     blank=True,
                                     verbose_name='Departamento'
                                     )
    modulos = models.ManyToManyField(
        'core.Modulo',
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha Creación', null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Última Actualización', null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="%(class)s_created", verbose_name='Creado Por')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="%(class)s_updated", verbose_name='Actualizado Por')

    history = HistoricalRecords()

    USERNAME_FIELD = 'username'

    def save(self, *args, **kwargs):
        if self.pk:
            cache_key = f"user_perms_synced_{self.pk}"
            cache.delete(cache_key)

        if self.username:
            self.username = self.username.upper()

        if self.first_name:
            self.first_name = self.first_name.upper()

        if self.last_name:
            self.last_name = self.last_name.upper()

        if self.email:
            self.email = self.email.lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        db_table = 'usuarios_usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['first_name']
