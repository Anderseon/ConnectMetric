from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import CandidateAssignment, ProcessStage, RecruitmentProcess, StageFeedback


class ProcessFlowTests(TestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.recruiter = user_model.objects.create_user(
            username="recruiter",
            email="recruiter@example.com",
            password="safe-pass-123",
        )
        self.recruiter.is_staff = True
        self.recruiter.save(update_fields=["is_staff"])
        self.candidate = user_model.objects.create_user(
            username="candidate",
            email="candidate@example.com",
            password="safe-pass-123",
        )
        self.observer = user_model.objects.create_user(
            username="observer",
            email="observer@example.com",
            password="safe-pass-123",
        )
        self.process = RecruitmentProcess.objects.create(title="Proceso QA", owner=self.recruiter)
        self.stage = ProcessStage.objects.create(process=self.process, name="Screening", order=1)
        self.assignment = CandidateAssignment.objects.create(
            process=self.process,
            candidate=self.candidate,
            current_stage=self.stage,
        )

    def test_only_staff_can_see_process_create(self) -> None:
        self.client.login(username="candidate", password="safe-pass-123")
        response = self.client.get(reverse("blog:process_create"))
        self.assertEqual(response.status_code, 403)

    def test_staff_creates_process(self) -> None:
        self.client.login(username="recruiter", password="safe-pass-123")
        response = self.client.post(
            reverse("blog:process_create"),
            data={
                "title": "Proceso Data",
                "description": "Contratación científico de datos",
                "status": "active",
                "start_date": "2025-10-01",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(RecruitmentProcess.objects.filter(title="Proceso Data", owner=self.recruiter).exists())

    def test_staff_assigns_candidate(self) -> None:
        self.client.login(username="recruiter", password="safe-pass-123")
        new_candidate = get_user_model().objects.create_user(
            username="newbie",
            email="newbie@example.com",
            password="safe-pass-123",
        )
        response = self.client.post(
            reverse("blog:assignment_create", args=[self.process.pk]),
            data={
                "candidate": new_candidate.pk,
                "current_stage": self.stage.pk,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            CandidateAssignment.objects.filter(
                process=self.process,
                candidate=new_candidate,
                current_stage=self.stage,
            ).exists()
        )

    def test_owner_updates_stage(self) -> None:
        self.client.login(username="recruiter", password="safe-pass-123")
        response = self.client.post(
            reverse("blog:stage_update", args=[self.process.pk, self.stage.pk]),
            data={
                "name": "Entrevista técnica",
                "order": 1,
                "description": "Panel con líderes",
                "due_date": "2025-10-20",
                "is_blocker": True,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.stage.refresh_from_db()
        self.assertTrue(self.stage.is_blocker)
        self.assertEqual(self.stage.description, "Panel con líderes")

    def test_process_list_requires_authentication(self) -> None:
        response = self.client.get(reverse("blog:process_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_candidate_can_submit_feedback(self) -> None:
        self.client.login(username="candidate", password="safe-pass-123")
        response = self.client.post(
            reverse("blog:submit_feedback", args=[self.assignment.pk, self.stage.pk]),
            data={
                "rating": 4,
                "comment": "Proceso ágil y respetuoso.",
                "visibility": "team",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        feedback = StageFeedback.objects.get(assignment=self.assignment, stage=self.stage)
        self.assertEqual(feedback.rating, 4)
        self.assertEqual(feedback.author, self.candidate)

    def test_feedback_edit_permissions(self) -> None:
        feedback = StageFeedback.objects.create(
            assignment=self.assignment,
            stage=self.stage,
            author=self.candidate,
            rating=5,
            comment="Muy buena experiencia",
        )
        self.assertTrue(feedback.is_editable_by(self.candidate))
        self.assertTrue(feedback.is_editable_by(self.recruiter))
        self.assertFalse(feedback.is_editable_by(self.observer))

    def test_metrics_requires_staff(self) -> None:
        self.client.login(username="candidate", password="safe-pass-123")
        response = self.client.get(reverse("blog:metrics"))
        self.assertEqual(response.status_code, 403)

    def test_metrics_dashboard_for_staff(self) -> None:
        self.client.login(username="recruiter", password="safe-pass-123")
        StageFeedback.objects.create(
            assignment=self.assignment,
            stage=self.stage,
            author=self.recruiter,
            rating=3,
            comment="Seguimiento mejorable",
        )
        response = self.client.get(reverse("blog:metrics"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("summary", response.context)
        summary = response.context["summary"]
        self.assertGreaterEqual(summary["total_processes"], 1)
        self.assertIn("best_rated_processes", response.context)

    def test_metrics_export_requires_staff(self) -> None:
        self.client.login(username="candidate", password="safe-pass-123")
        response = self.client.get(reverse("blog:metrics_export"))
        self.assertEqual(response.status_code, 403)

    def test_metrics_export_csv(self) -> None:
        self.client.login(username="recruiter", password="safe-pass-123")
        StageFeedback.objects.create(
            assignment=self.assignment,
            stage=self.stage,
            author=self.recruiter,
            rating=5,
            comment="Excelente trato",
        )
        response = self.client.get(reverse("blog:metrics_export"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("connectmetric_metrics_", response["Content-Disposition"])
        body = response.content.decode("utf-8")
        self.assertIn("Proceso QA", body)
