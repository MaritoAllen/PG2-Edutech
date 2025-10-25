# portal/forms.py
from django import forms
from academico.models import Actividad, Entrega, AsistenciaClase
from .models import Noticia, Notificacion

class ActividadForm(forms.ModelForm):
    class Meta:
        model = Actividad
        # 👇 Añade 'recurso_adjunto' a la lista 👇
        fields = ['titulo', 'descripcion', 'fecha_entrega', 'recurso_adjunto']
        widgets = {
            'fecha_entrega': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'descripcion': forms.Textarea(attrs={'rows': 5}), # Un poco más grande
            'recurso_adjunto': forms.ClearableFileInput(attrs={'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
            })

class EntregaForm(forms.ModelForm):
    class Meta:
        model = Entrega
        fields = ['archivo', 'comentarios']
        widgets = {
            'comentarios': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
            })

class CalificacionForm(forms.ModelForm):
    """
    Formulario para que el maestro califique una entrega.
    """
    class Meta:
        model = Entrega
        # Solo exponemos los campos que el maestro debe llenar
        fields = ['calificacion', 'comentarios_maestro']
        widgets = {
            'comentarios_maestro': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
            })


class NoticiaForm(forms.ModelForm):
    class Meta:
        model = Noticia
        fields = ['titulo', 'contenido', 'publicado']
        widgets = {
            'contenido': forms.Textarea(attrs={'rows': 10}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
            })

class NotificacionForm(forms.ModelForm):
    class Meta:
        model = Notificacion
        fields = ['audiencia', 'mensaje']
        widgets = {
            'mensaje': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Escribe tu mensaje corto aquí...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
            })

class AsistenciaForm(forms.Form):
    """
    Representa una sola fila en la hoja de asistencia.
    """
    # Usamos campos ocultos para saber a qué estudiante pertenece esta fila
    estudiante_id = forms.IntegerField(widget=forms.HiddenInput())
    
    # El campo 'estado' usará los 'choices' de nuestro modelo
    # y se renderizará como un grupo de radio buttons.
    estado = forms.ChoiceField(
        choices=AsistenciaClase.EstadoAsistencia.choices,
        widget=forms.RadioSelect,
        required=True
    )