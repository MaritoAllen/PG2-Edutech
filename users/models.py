# usuarios/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from academico.models import Curso

class User(AbstractUser):
    """
    Modelo de Usuario Personalizado.
    Hereda de AbstractUser para mantener todo el sistema de autenticación de Django,
    pero añade un campo 'user_type' para diferenciar roles.
    """
    class UserType(models.TextChoices):
        ESTUDIANTE = 'ESTUDIANTE', 'Estudiante'
        MAESTRO = 'MAESTRO', 'Maestro'
        ADMIN = 'ADMIN', 'Admin'
        # Puedes añadir más roles aquí en el futuro (ej. PADRE, SECRETARIA, etc.)

    # El campo 'username' de AbstractUser será el identificador principal
    # (ej. matrícula para estudiantes, código de empleado para maestros).
    user_type = models.CharField(
        max_length=20,
        choices=UserType.choices,
        verbose_name='Tipo de Usuario'
    )

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_user_type_display()})"

class Estudiante(models.Model):
    """
    Perfil para usuarios de tipo Estudiante.
    Contiene la información académica y personal específica de un estudiante.
    """
    # Relación uno a uno con el modelo de usuario. Si se elimina el usuario, se elimina el perfil.
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True, # El usuario es la clave primaria de este modelo.
        related_name='estudiante' # Para acceder desde el user: user.estudiante
    )
    
    matricula = models.CharField(max_length=20, unique=True, verbose_name='Matrícula')
    fecha_nacimiento = models.DateField(verbose_name='Fecha de Nacimiento')
    nombre_padre = models.CharField(max_length=100, verbose_name='Nombre del Padre o Tutor')
    telefono_contacto = models.CharField(max_length=15, blank=True, null=True, verbose_name='Teléfono de Contacto')
    direccion = models.TextField(blank=True, null=True, verbose_name='Dirección Residencial')
    contacto_emergencia = models.CharField(max_length=100, verbose_name='Contacto de Emergencia')
    enfermedades_alergias = models.TextField(blank=True, null=True, verbose_name='Enfermedades o Alergias')
    
    class Meta:
        verbose_name = 'Estudiante'
        verbose_name_plural = 'Estudiantes'

    def __str__(self):
        # Accedemos a los datos del modelo User relacionado
        return self.user.get_full_name()

class Maestro(models.Model):
    
    # --- NUEVA CLASE PARA EL ESTADO ---
    class EstadoMaestro(models.TextChoices):
        ACTIVO = 'ACTIVO', 'Activo'
        INACTIVO = 'INACTIVO', 'Inactivo'
        LICENCIA = 'LICENCIA', 'Con Licencia'

    # --- CAMPOS EXISTENTES ---
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='maestro'
    )
    numero_empleado = models.CharField(max_length=20, unique=True, verbose_name='Número de Empleado')
    especialidad = models.CharField(max_length=100, verbose_name='Especialidad Principal (Ej. Matemáticas)')
    fecha_contratacion = models.DateField(verbose_name='Fecha de Contratación')
    telefono_contacto = models.CharField(max_length=20, blank=True, verbose_name='Teléfono Principal')
    cursos = models.ManyToManyField(
        Curso,
        blank=True,
        related_name='maestros',
        verbose_name='Cursos Asignados'
    )

    # --- NUEVOS CAMPOS PARA EL PERFIL PROFESIONAL ---
    
    # Campo para una foto
    foto_perfil = models.ImageField(
        upload_to='fotos_perfil/maestros/', 
        null=True, 
        blank=True, 
        verbose_name="Foto de Perfil"
    )
    
    # Información Académica
    titulo_academico = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="Título Académico Principal"
    )
    
    # Información Pública/Personal
    biografia = models.TextField(
        blank=True, 
        verbose_name="Biografía Corta / Resumen Profesional"
    )
    direccion = models.TextField(
        blank=True, 
        verbose_name="Dirección de Contacto"
    )

    # Información de Emergencia
    contacto_emergencia_nombre = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name="Nombre de Contacto de Emergencia"
    )
    contacto_emergencia_telefono = models.CharField(
        max_length=20, 
        blank=True, 
        verbose_name="Teléfono de Emergencia"
    )
    
    # Información Administrativa
    estado = models.CharField(
        max_length=10, 
        choices=EstadoMaestro.choices, 
        default=EstadoMaestro.ACTIVO,
        verbose_name="Estado Administrativo"
    )

    class Meta:
        verbose_name = 'Maestro'
        verbose_name_plural = 'Maestros'

    def __str__(self):
        return self.user.get_full_name()
