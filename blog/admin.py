from django.contrib import admin

from .models import CandidateAssignment, Post, ProcessStage, RecruitmentProcess, StageFeedback


class ProcessStageInline(admin.TabularInline):
	model = ProcessStage
	extra = 1
	ordering = ("order",)


class CandidateAssignmentInline(admin.TabularInline):
	model = CandidateAssignment
	extra = 0
	autocomplete_fields = ("candidate",)


@admin.register(RecruitmentProcess)
class RecruitmentProcessAdmin(admin.ModelAdmin):
	list_display = ("title", "owner", "status", "start_date", "end_date", "stage_count", "candidate_count")
	list_filter = ("status", "start_date", "end_date")
	search_fields = ("title", "owner__username", "owner__email")
	ordering = ("-created_at",)
	inlines = [ProcessStageInline, CandidateAssignmentInline]

	@admin.display(description="Etapas")
	def stage_count(self, obj: RecruitmentProcess) -> int:
		return obj.stages.count()

	@admin.display(description="Candidatos")
	def candidate_count(self, obj: RecruitmentProcess) -> int:
		return obj.assignments.count()


@admin.register(ProcessStage)
class ProcessStageAdmin(admin.ModelAdmin):
	list_display = ("name", "process", "order", "due_date", "is_blocker")
	list_filter = ("is_blocker", "due_date")
	search_fields = ("name", "process__title")
	ordering = ("process", "order")


@admin.register(CandidateAssignment)
class CandidateAssignmentAdmin(admin.ModelAdmin):
	list_display = ("candidate", "process", "current_stage", "joined_at")
	search_fields = ("candidate__username", "candidate__email", "process__title")
	autocomplete_fields = ("candidate", "process", "current_stage")
	ordering = ("-joined_at",)


@admin.register(StageFeedback)
class StageFeedbackAdmin(admin.ModelAdmin):
	list_display = ("assignment", "stage", "author", "rating", "visibility", "created_at")
	list_filter = ("visibility", "rating", "created_at")
	search_fields = (
		"assignment__candidate__username",
		"assignment__process__title",
		"author__username",
		"comment",
	)
	autocomplete_fields = ("assignment", "stage", "author")
	ordering = ("-created_at",)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
	list_display = ("title", "author", "published_date")
	search_fields = ("title", "author__username")
	ordering = ("-published_date",)