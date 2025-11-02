from django.contrib import admin
from .models import Competencia, Planificacion, Curso, Clase, PeriodoAcademico

# Register your models here.
admin.site.register(Competencia)
admin.site.register(Planificacion)
admin.site.register(Curso)
admin.site.register(Clase)
admin.site.register(PeriodoAcademico)