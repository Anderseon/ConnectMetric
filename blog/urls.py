from django.urls import path

from . import views

app_name = "blog"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("publicaciones/", views.post_list, name="publicaciones"),
    path("metricas/", views.metrics_dashboard, name="metrics"),
    path("metricas/exportar/", views.metrics_export_csv, name="metrics_export"),
    path("procesos/", views.process_list, name="process_list"),
    path("procesos/nuevo/", views.process_create, name="process_create"),
    path("procesos/<int:pk>/", views.process_detail, name="process_detail"),
    path("procesos/<int:pk>/editar/", views.process_update, name="process_update"),
    path("procesos/<int:pk>/etapas/nueva/", views.stage_create, name="stage_create"),
    path(
        "procesos/<int:pk>/etapas/<int:stage_id>/editar/",
        views.stage_update,
        name="stage_update",
    ),
    path("procesos/<int:pk>/asignaciones/nueva/", views.assignment_create, name="assignment_create"),
    path(
        "procesos/<int:pk>/asignaciones/<int:assignment_id>/avanzar/",
        views.assignment_progress,
        name="assignment_progress",
    ),
    path(
        "asignaciones/<int:assignment_id>/etapas/<int:stage_id>/feedback/",
        views.submit_feedback,
        name="submit_feedback",
    ),
]