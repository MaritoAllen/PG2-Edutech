from django.urls import path
from . import views

urlpatterns = [
    path('estudiante/', views.PortalEstudianteView.as_view(), name='portal_estudiante'),
    path('maestro/', views.PortalMaestroView.as_view(), name='portal_maestro'),
    path('clase/<int:clase_pk>/crear-actividad/', views.ActividadCreateView.as_view(), name='actividad_create'),
    path('actividad/<int:pk>/', views.ActividadDetailView.as_view(), name='actividad_detail'),
    path('actividad/<int:pk>/entregas/', views.ActividadEntregasView.as_view(), name='actividad_entregas'),
    path('entrega/<int:pk>/calificar/', views.CalificarEntregaView.as_view(), name='calificar_entrega'),
    path('admin/', views.PortalAdminView.as_view(), name='portal_admin'),
    path('noticias/nueva/', views.NoticiaCreateView.as_view(), name='noticia_create'),
    path('noticias/<int:pk>/editar/', views.NoticiaUpdateView.as_view(), name='noticia_update'),
    path('noticias/<int:pk>/eliminar/', views.NoticiaDeleteView.as_view(), name='noticia_delete'),
    path('clase/<int:clase_pk>/asistencia/', views.TomarAsistenciaView.as_view(), name='tomar_asistencia'),
    path('clase/<int:clase_pk>/asistencia/<str:fecha>/', views.TomarAsistenciaView.as_view(), name='tomar_asistencia_fecha'),
]