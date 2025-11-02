from django.contrib import admin
from .models import User, Estudiante, Maestro, PadreDeFamilia
from django.contrib.auth.admin import UserAdmin
from .forms import CustomUserCreationForm, CustomUserChangeForm

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm      # <-- Ahora este formulario está correcto
    model = User
    
    list_display = (
        'username', 'email', 'first_name', 'last_name', 
        'user_type', 'is_staff'
    )
    
    # Esto controla el formulario de AÑADIR
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('user_type',)}),
    )

admin.site.register(User, CustomUserAdmin)
admin.site.register(Estudiante)
admin.site.register(Maestro)
admin.site.register(PadreDeFamilia)