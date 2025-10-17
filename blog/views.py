import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Avg, Count, Prefetch, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _

from .forms import CandidateAssignmentForm, ProcessStageForm, RecruitmentProcessForm, StageFeedbackForm
from .models import (
    CandidateAssignment,
    Post,
    ProcessStage,
    RecruitmentProcess,
    StageFeedback,
)


@login_required
def dashboard(request):
    owned_processes = (
        RecruitmentProcess.objects.filter(owner=request.user)
        .annotate(stage_total=Count("stages", distinct=True), candidate_total=Count("assignments", distinct=True))
        .order_by("-created_at")
    )

    candidate_assignments = (
        CandidateAssignment.objects.filter(candidate=request.user)
        .select_related("process", "current_stage")
        .prefetch_related("feedbacks__stage")
        .order_by("-joined_at")
    )

    recent_feedback = (
        StageFeedback.objects.filter(author=request.user)
        .select_related("stage", "assignment__process")
        .order_by("-created_at")[:5]
    )

    context = {
        "owned_processes": owned_processes,
        "candidate_assignments": candidate_assignments,
        "recent_feedback": recent_feedback,
    }
    return render(request, "blog/dashboard.html", context)


@login_required
def process_list(request):
    processes = (
        RecruitmentProcess.objects.select_related("owner")
        .annotate(
            stage_total=Count("stages", distinct=True),
            candidate_total=Count("assignments", distinct=True),
            average_rating=Avg("assignments__feedbacks__rating"),
        )
        .order_by("-created_at")
    )
    return render(
        request,
        "blog/process_list.html",
        {
            "processes": processes,
            "can_manage": request.user.is_staff,
        },
    )


@login_required
def process_detail(request, pk: int):
    assignment_qs = CandidateAssignment.objects.select_related("candidate", "current_stage").prefetch_related(
        "feedbacks__stage",
        "feedbacks__author",
    )

    process = get_object_or_404(
        RecruitmentProcess.objects.select_related("owner").prefetch_related(
            "stages",
            Prefetch("assignments", queryset=assignment_qs),
        ),
        pk=pk,
    )

    stage_metrics = {
        item["stage_id"]: item
        for item in StageFeedback.objects.filter(stage__process=process)
        .values("stage_id")
        .annotate(avg_rating=Avg("rating"), responses=Count("id"))
    }

    stages = []
    for stage in process.stages.all():
        metrics = stage_metrics.get(stage.id, {})
        stage.avg_rating = metrics.get("avg_rating")
        stage.responses = metrics.get("responses", 0)
        stages.append(stage)

    assignments = list(process.assignments.all())
    assignment_form = None
    if can_manage := (request.user.is_staff or request.user == process.owner):
        assignment_form = CandidateAssignmentForm(process=process)

    context = {
        "process": process,
        "stages": stages,
        "assignments": assignments,
        "assignment_form": assignment_form,
        "can_manage": request.user.is_staff or request.user == process.owner,
    }
    return render(request, "blog/process_detail.html", context)


@login_required
def process_create(request):
    if not request.user.is_staff:
        raise PermissionDenied()

    if request.method == "POST":
        form = RecruitmentProcessForm(request.POST)
        if form.is_valid():
            process = form.save(commit=False)
            process.owner = request.user
            process.save()
            messages.success(request, "Proceso creado correctamente.")
            return redirect("blog:process_detail", pk=process.pk)
    else:
        form = RecruitmentProcessForm()

    return render(request, "blog/process_form.html", {"form": form, "process": None})


@login_required
def process_update(request, pk: int):
    process = get_object_or_404(RecruitmentProcess, pk=pk)
    if not (request.user.is_staff or request.user == process.owner):
        raise PermissionDenied()

    if request.method == "POST":
        form = RecruitmentProcessForm(request.POST, instance=process)
        if form.is_valid():
            form.save()
            messages.success(request, "Proceso actualizado.")
            return redirect("blog:process_detail", pk=process.pk)
    else:
        form = RecruitmentProcessForm(instance=process)

    return render(request, "blog/process_form.html", {"form": form, "process": process})


@login_required
def stage_create(request, pk: int):
    process = get_object_or_404(RecruitmentProcess, pk=pk)
    if not (request.user.is_staff or request.user == process.owner):
        raise PermissionDenied()

    if request.method == "POST":
        form = ProcessStageForm(request.POST)
        if form.is_valid():
            stage = form.save(commit=False)
            stage.process = process
            stage.save()
            messages.success(request, "Etapa registrada.")
            return redirect("blog:process_detail", pk=process.pk)
    else:
        form = ProcessStageForm()

    return render(request, "blog/stage_form.html", {"form": form, "process": process, "stage": None})


@login_required
def stage_update(request, pk: int, stage_id: int):
    process = get_object_or_404(RecruitmentProcess, pk=pk)
    stage = get_object_or_404(ProcessStage, pk=stage_id, process=process)
    if not (request.user.is_staff or request.user == process.owner):
        raise PermissionDenied()

    if request.method == "POST":
        form = ProcessStageForm(request.POST, instance=stage)
        if form.is_valid():
            form.save()
            messages.success(request, "Etapa actualizada.")
            return redirect("blog:process_detail", pk=process.pk)
    else:
        form = ProcessStageForm(instance=stage)

    return render(
        request,
        "blog/stage_form.html",
        {
            "form": form,
            "process": process,
            "stage": stage,
        },
    )


@login_required
@transaction.atomic
def assignment_create(request, pk: int):
    process = get_object_or_404(RecruitmentProcess, pk=pk)
    if not (request.user.is_staff or request.user == process.owner):
        raise PermissionDenied()

    if request.method == "POST":
        form = CandidateAssignmentForm(request.POST, process=process)
        form.process = process
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.process = process
            assignment.save()
            if assignment.current_stage:
                process.assignments.filter(candidate=assignment.candidate).update(current_stage=assignment.current_stage)
            messages.success(request, "Candidato asignado al proceso.")
        else:
            messages.error(request, "Revisa los datos del formulario.")
    return redirect("blog:process_detail", pk=process.pk)


@login_required
def assignment_progress(request, pk: int, assignment_id: int):
    assignment = get_object_or_404(
        CandidateAssignment.objects.select_related("process", "candidate", "current_stage"),
        pk=assignment_id,
        process_id=pk,
    )
    process = assignment.process
    if not (request.user.is_staff or request.user == process.owner):
        raise PermissionDenied()

    next_stage = (
        process.stages.filter(order__gt=assignment.current_stage.order if assignment.current_stage else 0)
        .order_by("order")
        .first()
    )

    if next_stage:
        assignment.current_stage = next_stage
        assignment.save(update_fields=["current_stage"])
        messages.success(request, f"{assignment.candidate} avanza a {next_stage.name}.")
    else:
        assignment.current_stage = None
        assignment.save(update_fields=["current_stage"])
        messages.info(request, f"{assignment.candidate} completó todas las etapas.")

    return redirect("blog:process_detail", pk=process.pk)


@login_required
def submit_feedback(request, assignment_id: int, stage_id: int):
    assignment = get_object_or_404(
        CandidateAssignment.objects.select_related("process", "candidate", "current_stage"),
        pk=assignment_id,
        candidate=request.user,
    )
    stage = get_object_or_404(ProcessStage, pk=stage_id, process=assignment.process)

    existing_feedback = StageFeedback.objects.filter(
        assignment=assignment,
        stage=stage,
        author=request.user,
    ).first()

    if request.method == "POST":
        form = StageFeedbackForm(request.POST, instance=existing_feedback)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.assignment = assignment
            feedback.stage = stage
            feedback.author = request.user
            feedback.save()
            messages.success(request, "Tu experiencia quedó registrada.")
            return redirect("blog:process_detail", pk=assignment.process.pk)
    else:
        form = StageFeedbackForm(instance=existing_feedback)

    context = {
        "assignment": assignment,
        "stage": stage,
        "form": form,
    }
    return render(request, "blog/submit_feedback.html", context)


@login_required
def post_list(request):
    posts = Post.objects.select_related("author").order_by("-published_date")
    return render(request, "blog/post_list.html", {"posts": posts})


@login_required
def metrics_dashboard(request):
    if not request.user.is_staff:
        raise PermissionDenied()

    process_qs = RecruitmentProcess.objects.all()

    summary = {
        "total_processes": process_qs.count(),
        "active_processes": process_qs.filter(status="active").count(),
        "closed_processes": process_qs.filter(status="closed").count(),
        "candidate_assignments": CandidateAssignment.objects.count(),
        "feedback_records": StageFeedback.objects.count(),
    }

    process_metrics = process_qs.annotate(
        avg_rating=Avg("assignments__feedbacks__rating"),
        assignment_total=Count("assignments", distinct=True),
        stage_total=Count("stages", distinct=True),
        feedback_total=Count("assignments__feedbacks", distinct=True),
        completed_assignments=Count(
            "assignments",
            filter=Q(assignments__current_stage__isnull=True),
            distinct=True,
        ),
    ).order_by("-created_at")

    best_rated_processes = [proc for proc in process_metrics if proc.feedback_total]
    best_rated_processes.sort(key=lambda proc: proc.avg_rating or 0, reverse=True)
    best_rated_processes = best_rated_processes[:5]

    stage_metrics = (
        ProcessStage.objects.select_related("process")
        .annotate(
            avg_rating=Avg("feedback__rating"),
            feedback_total=Count("feedback", distinct=True),
        )
        .order_by("process__title", "order")
    )

    stages_to_watch = (
        stage_metrics.filter(feedback_total__gt=0).order_by("avg_rating")[:5]
    )

    assignment_summary = {
        "total": CandidateAssignment.objects.count(),
        "completed": CandidateAssignment.objects.filter(current_stage__isnull=True).count(),
    }
    assignment_summary["in_progress"] = assignment_summary["total"] - assignment_summary["completed"]
    if assignment_summary["total"]:
        assignment_summary["completed_percentage"] = round(
            assignment_summary["completed"] * 100 / assignment_summary["total"],
            2,
        )
    else:
        assignment_summary["completed_percentage"] = 0

    context = {
        "summary": summary,
        "process_metrics": process_metrics,
        "best_rated_processes": best_rated_processes,
        "stage_metrics": stage_metrics,
        "stages_to_watch": stages_to_watch,
        "assignment_summary": assignment_summary,
    }
    return render(request, "blog/metrics_dashboard.html", context)


@login_required
def metrics_export_csv(request):
    if not request.user.is_staff:
        raise PermissionDenied()

    filename = f"connectmetric_metrics_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f"attachment; filename={filename}"

    writer = csv.writer(response)
    writer.writerow(
        [
            _("Proceso"),
            _("Responsable"),
            _("Estado"),
            _("Candidatos"),
            _("Etapas"),
            _("Feedback"),
            _("Rating promedio"),
            _("Candidatos completados"),
        ]
    )

    process_metrics = (
        RecruitmentProcess.objects.select_related("owner")
        .annotate(
            avg_rating=Avg("assignments__feedbacks__rating"),
            assignment_total=Count("assignments", distinct=True),
            stage_total=Count("stages", distinct=True),
            feedback_total=Count("assignments__feedbacks", distinct=True),
            completed_assignments=Count(
                "assignments",
                filter=Q(assignments__current_stage__isnull=True),
                distinct=True,
            ),
        )
        .order_by("-created_at")
    )

    for process in process_metrics:
        writer.writerow(
            [
                process.title,
                process.owner.get_full_name() or process.owner.username,
                process.get_status_display(),
                process.assignment_total,
                process.stage_total,
                process.feedback_total,
                f"{process.avg_rating:.2f}" if process.avg_rating is not None else "",
                process.completed_assignments,
            ]
        )

    return response