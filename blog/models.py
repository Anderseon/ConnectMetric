"""Domain models for ConnectMetric recruitment workflows."""

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

User = get_user_model()


class Post(models.Model):
    """Legacy blog post model used for announcements inside the platform."""

    title = models.CharField(max_length=200, verbose_name="Título")
    content = models.TextField(verbose_name="Contenido")
    published_date = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Publicación")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Autor")

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return self.title

    class Meta:
        verbose_name = "Publicación"
        verbose_name_plural = "Publicaciones"
        ordering = ["-published_date"]


class RecruitmentProcess(models.Model):
    """Selection process created by HR or hiring managers."""

    STATUS_CHOICES = [
        ("draft", "Borrador"),
        ("active", "Activo"),
        ("on_hold", "En pausa"),
        ("closed", "Cerrado"),
    ]

    title = models.CharField(max_length=200, verbose_name="Nombre del proceso")
    description = models.TextField(verbose_name="Descripción", blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="processes", verbose_name="Responsable")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    start_date = models.DateField(null=True, blank=True, verbose_name="Fecha de inicio")
    end_date = models.DateField(null=True, blank=True, verbose_name="Fecha de cierre")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Proceso de selección"
        verbose_name_plural = "Procesos de selección"
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover - representation only
        return self.title

    @property
    def total_stages(self) -> int:
        return self.stages.count()


class ProcessStage(models.Model):
    """Stage that belongs to a recruitment process (screening, técnica, etc.)."""

    process = models.ForeignKey(
        RecruitmentProcess,
        on_delete=models.CASCADE,
        related_name="stages",
        verbose_name="Proceso",
    )
    name = models.CharField(max_length=150, verbose_name="Nombre de la etapa")
    order = models.PositiveIntegerField(verbose_name="Orden")
    description = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True, verbose_name="Fecha objetivo")
    is_blocker = models.BooleanField(default=False, verbose_name="Bloquea avance")

    class Meta:
        verbose_name = "Etapa"
        verbose_name_plural = "Etapas"
        ordering = ["order"]
        unique_together = ("process", "order")

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.process.title} - {self.name}"


class CandidateAssignment(models.Model):
    """Relationship between a candidate and a recruitment process."""

    process = models.ForeignKey(
        RecruitmentProcess,
        on_delete=models.CASCADE,
        related_name="assignments",
        verbose_name="Proceso",
    )
    candidate = models.ForeignKey(User, on_delete=models.CASCADE, related_name="candidate_assignments")
    joined_at = models.DateTimeField(auto_now_add=True)
    current_stage = models.ForeignKey(
        ProcessStage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="current_assignments",
    )

    class Meta:
        verbose_name = "Asignación de candidato"
        verbose_name_plural = "Asignaciones de candidatos"
        unique_together = ("process", "candidate")

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.candidate.get_full_name() or self.candidate.username} → {self.process.title}"

    def completed_stages(self) -> models.QuerySet["StageFeedback"]:
        return self.feedbacks.select_related("stage")


class StageFeedback(models.Model):
    """Feedback que deja un candidato sobre una etapa."""

    assignment = models.ForeignKey(
        CandidateAssignment,
        on_delete=models.CASCADE,
        related_name="feedbacks",
        verbose_name="Asignación",
    )
    stage = models.ForeignKey(ProcessStage, on_delete=models.CASCADE, related_name="feedback")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="stage_feedback")
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Califica utilidad de la etapa (1-5)",
    )
    comment = models.TextField()
    visibility = models.CharField(
        max_length=20,
        choices=[("team", "Equipo"), ("candidates", "Candidatos"), ("private", "Privado PO")],
        default="candidates",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Feedback de etapa"
        verbose_name_plural = "Feedback de etapas"
        unique_together = ("assignment", "stage")
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover
        return f"Feedback {self.stage.name} - {self.assignment.candidate}"

    def is_editable_by(self, user: User) -> bool:
        return user == self.author or user.is_staff