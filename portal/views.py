from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView, CreateView, FormView, DetailView, UpdateView, DeleteView, ListView
from academico.models import Clase, PeriodoAcademico, Actividad, Entrega, AsistenciaClase
from .forms import ActividadForm, EntregaForm, CalificacionForm, NoticiaForm, NotificacionForm, AsistenciaForm
from portal.models import Noticia
from users.models import User
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse_lazy, reverse
from django.db.models import Exists, OuterRef, Subquery, DecimalField
from django.db.models import Q
from .models import Notificacion
from django.utils import timezone
from django.forms import formset_factory
from django.views import View

class PortalEstudianteView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Muestra el portal principal para el estudiante, incluyendo su horario de clases
    para el periodo académico actual.
    """
    template_name = 'portal/portal_estudiante.html'

    def test_func(self):
        # 1. Condición de seguridad: ¿El usuario es un estudiante?
        return self.request.user.user_type == User.UserType.ESTUDIANTE

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtenemos el perfil del estudiante del usuario que ha iniciado sesión
        estudiante = self.request.user.estudiante
        
        # 2. Lógica para encontrar el periodo académico actual
        # (Simplificación: tomamos el último periodo creado como el actual)
        periodo_actual = PeriodoAcademico.objects.order_by('-fecha_inicio').first()

        clases_inscritas = []
        if periodo_actual:
            # 3. Filtramos las clases en las que el estudiante está inscrito para el periodo actual
            clases_inscritas = Clase.objects.filter(
                estudiantes=estudiante,
                periodo=periodo_actual
            ).select_related('curso', 'maestro__user').order_by('dia_semana', 'hora_inicio')
            
            subquery_entrega = Entrega.objects.filter(
                actividad=OuterRef('pk'), 
                estudiante=estudiante
            )

            subquery_calificacion = subquery_entrega.values('calificacion')[:1]

            
            actividades = Actividad.objects.filter(
                clase__in=clases_inscritas
            ).select_related('clase__curso').annotate(
                fue_entregada=Exists(subquery_entrega),
                calificacion_obtenida=Subquery(subquery_calificacion, output_field=DecimalField())
            ).order_by('fecha_entrega')


        context['estudiante'] = estudiante
        context['clases_inscritas'] = clases_inscritas
        context['periodo_actual'] = periodo_actual
        context['actividades'] = actividades
        context['titulo'] = 'Mi Portal de Estudiante'
        context['notificaciones'] = Notificacion.objects.filter(
            Q(audiencia=Notificacion.TargetAudiencia.TODOS) |
            Q(audiencia=Notificacion.TargetAudiencia.ESTUDIANTES)
        ).order_by('-fecha_envio')[:5] # Muestra las 5 más recientes
        
        return context
    
class PortalMaestroView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Muestra el portal principal para el maestro, con la lista de clases
    que imparte en el periodo académico actual.
    """
    template_name = 'portal/portal_maestro.html'

    def test_func(self):
        # Condición de seguridad: ¿El usuario es un maestro?
        return self.request.user.user_type == User.UserType.MAESTRO

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtenemos el perfil del maestro que ha iniciado sesión
        maestro = self.request.user.maestro
        
        # Buscamos el periodo académico actual
        periodo_actual = PeriodoAcademico.objects.order_by('-fecha_inicio').first()

        clases_asignadas = []
        if periodo_actual:
            # Filtramos las clases asignadas al maestro para el periodo actual
            # Usamos prefetch_related para obtener los estudiantes de forma eficiente
            clases_asignadas = Clase.objects.filter(
                maestro=maestro,
                periodo=periodo_actual
            ).select_related('curso').prefetch_related('estudiantes__user').order_by('dia_semana', 'hora_inicio')

        context['maestro'] = maestro
        context['clases_asignadas'] = clases_asignadas
        context['periodo_actual'] = periodo_actual
        context['titulo'] = 'Mi Portal de Maestro'
        context['notificaciones'] = Notificacion.objects.filter(
            Q(audiencia=Notificacion.TargetAudiencia.TODOS) |
            Q(audiencia=Notificacion.TargetAudiencia.MAESTROS)
        ).order_by('-fecha_envio')[:5] # Muestra las 5 más recientes
        
        return context

@login_required
def portal_redirect_view(request):
    """
    Redirige al usuario a su portal correspondiente después de iniciar sesión.
    """
    if request.user.user_type == User.UserType.ESTUDIANTE:
        return redirect('portal_estudiante')
    elif request.user.user_type == User.UserType.MAESTRO:
        return redirect('portal_maestro')
    elif request.user.is_superuser or request.user.user_type == User.UserType.ADMIN:
        # Si es un superusuario o admin, lo enviamos al panel de administración
        return redirect('admin:index')
    else:
        # Puedes definir una página por defecto para otros casos si los tienes
        return redirect('página_de_error_o_inicio_general')

class ActividadCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Actividad
    form_class = ActividadForm
    template_name = 'portal/actividad_form.html'

    def test_func(self):
        # El usuario debe ser maestro Y el maestro de la clase
        clase = get_object_or_404(Clase, pk=self.kwargs['clase_pk'])
        return self.request.user.user_type == User.UserType.MAESTRO and clase.maestro == self.request.user.maestro

    def form_valid(self, form):
        # Asignamos la clase a la actividad antes de guardarla
        clase = get_object_or_404(Clase, pk=self.kwargs['clase_pk'])
        form.instance.clase = clase
        return super().form_valid(form)

    def get_success_url(self):
        # Redirige de vuelta al portal del maestro (o a una vista de detalle de la clase)
        return reverse_lazy('portal_maestro')
    
class ActividadDetailView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = 'portal/actividad_detail.html'
    form_class = EntregaForm

    def test_func(self):
        # Solo estudiantes pueden ver esta página
        return self.request.user.user_type == User.UserType.ESTUDIANTE

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        actividad = get_object_or_404(Actividad, pk=self.kwargs['pk'])
        estudiante = self.request.user.estudiante
        
        # Buscamos si ya existe una entrega para mostrarla
        entrega_existente = Entrega.objects.filter(actividad=actividad, estudiante=estudiante).first()

        # Asignamos las variables al contexto para usarlas en la plantilla
        context['actividad'] = actividad
        context['entrega_existente'] = entrega_existente
        return context

    def form_valid(self, form):
        actividad = get_object_or_404(Actividad, pk=self.kwargs['pk'])
        estudiante = self.request.user.estudiante

        # Usamos update_or_create para manejar tanto la primera entrega como las re-entregas
        Entrega.objects.update_or_create(
            actividad=actividad,
            estudiante=estudiante,
            defaults={
                'archivo': form.cleaned_data.get('archivo'), # Usar .get() es más seguro
                'comentarios': form.cleaned_data.get('comentarios')
            }
        )
        return redirect('portal_estudiante')

class ActividadEntregasView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    Muestra los detalles de una actividad y una lista de todas las entregas
    de los estudiantes para que el maestro las califique.
    """
    model = Actividad
    template_name = 'portal/actividad_entregas.html'
    context_object_name = 'actividad'

    def test_func(self):
        # Seguridad: Solo el maestro de la clase puede ver esta página
        actividad = self.get_object()
        return self.request.user.user_type == User.UserType.MAESTRO and actividad.clase.maestro == self.request.user.maestro

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtenemos todas las entregas asociadas a esta actividad
        context['entregas'] = self.object.entregas.all().select_related('estudiante__user')
        return context

class CalificarEntregaView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Muestra el formulario para calificar una entrega específica.
    """
    model = Entrega
    form_class = CalificacionForm
    template_name = 'portal/calificar_entrega_form.html'
    context_object_name = 'entrega'

    def test_func(self):
        # Seguridad: Solo el maestro de la clase puede calificar
        entrega = self.get_object()
        return self.request.user.user_type == User.UserType.MAESTRO and entrega.actividad.clase.maestro == self.request.user.maestro

    def get_success_url(self):
        # Redirige de vuelta a la lista de entregas de la actividad
        return reverse('actividad_entregas', kwargs={'pk': self.object.actividad.pk})

class PortalAdminView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    Muestra el portal principal del Administrador.
    Usamos ListView para mostrar la lista de noticias recientes.
    """
    model = Noticia
    template_name = 'portal/portal_admin.html'
    context_object_name = 'noticias'
    paginate_by = 5 # Muestra 5 noticias por página

    def test_func(self):
        # Seguridad: Solo usuarios de tipo ADMIN pueden entrar
        return self.request.user.user_type == User.UserType.ADMIN

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Portal Administrativo'
        
        # 👇 Añadimos el formulario de notificación al contexto 👇
        context['notificacion_form'] = NotificacionForm() 
        return context

    def post(self, request, *args, **kwargs):
        """Maneja el envío del formulario de notificaciones."""
        form = NotificacionForm(request.POST)
        if form.is_valid():
            # Creamos la notificación pero no la guardamos aún
            notificacion = form.save(commit=False)
            notificacion.autor = request.user
            notificacion.save()
            
            # (Opcional: añadir un mensaje de éxito con Django messages)
            return redirect('portal_admin')
        else:
            # Si el formulario es inválido, recargamos la página
            # (una mejor implementación pasaría el formulario con errores)
            return self.get(request, *args, **kwargs)

# 2. CRUD PARA LAS NOTICIAS
class NoticiaCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Noticia
    form_class = NoticiaForm
    template_name = 'portal/noticia_form.html'
    success_url = reverse_lazy('portal_admin')

    def test_func(self):
        return self.request.user.user_type == User.UserType.ADMIN

    def form_valid(self, form):
        # Asignamos al autor automáticamente
        form.instance.autor = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Publicar Nueva Noticia'
        return context

class NoticiaUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Noticia
    form_class = NoticiaForm
    template_name = 'portal/noticia_form.html'
    success_url = reverse_lazy('portal_admin')

    def test_func(self):
        # Solo el autor o un superusuario puede editar (o puedes quitar esta línea)
        return self.request.user == self.get_object().autor or self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Noticia'
        return context

class NoticiaDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Noticia
    template_name = 'portal/noticia_confirm_delete.html'
    success_url = reverse_lazy('portal_admin')

    def test_func(self):
        return self.request.user == self.get_object().autor or self.request.user.is_superuser
    
AsistenciaFormSet = formset_factory(AsistenciaForm, extra=0) # extra=0 evita formularios vacíos

class TomarAsistenciaView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'portal/tomar_asistencia.html'

    def test_func(self):
        return self.request.user.user_type == User.UserType.MAESTRO

    def get_clase(self):
        return get_object_or_404(
            Clase, 
            pk=self.kwargs['clase_pk'], 
            maestro=self.request.user.maestro
        )

    def get_fecha_seleccionada(self):
        """
        Obtiene la fecha de la URL, o usa la fecha de hoy si no hay.
        """
        fecha_str = self.kwargs.get('fecha')
        if fecha_str:
            try:
                # Convierte el string YYYY-MM-DD a un objeto date
                return datetime.strptime(fecha_str, '%Y-%m-%d').date()
            except ValueError:
                pass # Si el formato es incorrecto, usa hoy
        return timezone.now().date()

    def get(self, request, *args, **kwargs):
        """Maneja la carga de la página (petición GET)."""
        clase = self.get_clase()
        fecha_seleccionada = self.get_fecha_seleccionada() # 👈 Usa la nueva función
        
        estudiantes = clase.estudiantes.all().select_related('user')
        
        # Busca la asistencia de la FECHA SELECCIONADA
        asistencia_dia = AsistenciaClase.objects.filter(clase=clase, fecha=fecha_seleccionada)
        asistencia_map = {a.estudiante_id: a.estado for a in asistencia_dia}
        
        initial_data = []
        estudiantes_data = []
        
        for est in estudiantes:
            estado_actual = asistencia_map.get(est.pk, 'A') # Ausente por defecto
            initial_data.append({'estudiante_id': est.pk, 'estado': estado_actual})
            estudiantes_data.append({'nombre': est.user.get_full_name(), 'id': est.pk})

        formset = AsistenciaFormSet(initial=initial_data)
        alumnos_con_form = zip(estudiantes_data, formset)

        # --- Lógica de Navegación de Fechas ---
        fecha_anterior = fecha_seleccionada - timedelta(days=1)
        fecha_siguiente = fecha_seleccionada + timedelta(days=1)
        es_hoy = (fecha_seleccionada == timezone.now().date())

        context = {
            'clase': clase,
            'formset': formset,
            'alumnos_con_form': alumnos_con_form,
            'fecha_seleccionada': fecha_seleccionada, # 👈 Pasa la fecha seleccionada
            'fecha_anterior_str': fecha_anterior.isoformat(),  # YYYY-MM-DD
            'fecha_siguiente_str': fecha_siguiente.isoformat(), # YYYY-MM-DD
            'es_hoy': es_hoy,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """Maneja el envío del formulario (petición POST)."""
        clase = self.get_clase()
        fecha_seleccionada = self.get_fecha_seleccionada() # 👈 Usa la nueva función
        
        formset = AsistenciaFormSet(request.POST)

        if formset.is_valid():
            for form_data in formset.cleaned_data:
                estudiante_id = form_data['estudiante_id']
                estado = form_data['estado']
                
                # Guarda la asistencia con la FECHA SELECCIONADA
                AsistenciaClase.objects.update_or_create(
                    clase=clase,
                    estudiante_id=estudiante_id,
                    fecha=fecha_seleccionada, # 👈 Guarda en la fecha correcta
                    defaults={'estado': estado}
                )
            
            # Redirige de vuelta al portal del maestro
            return redirect('portal_maestro')
        
        # Si hay errores, vuelve a cargar la página
        return self.get(request, *args, **kwargs)