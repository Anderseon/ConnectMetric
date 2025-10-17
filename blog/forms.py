from django import forms

from django.contrib.auth import get_user_model

from .models import CandidateAssignment, ProcessStage, RecruitmentProcess, StageFeedback


class StageFeedbackForm(forms.ModelForm):
    class Meta:
        model = StageFeedback
        fields = ("rating", "comment", "visibility")
        widgets = {
            "rating": forms.NumberInput(attrs={"min": 1, "max": 5, "type": "range", "class": "form-range"}),
            "comment": forms.Textarea(attrs={"rows": 4, "class": "form-control", "placeholder": "Comparte tu experiencia"}),
            "visibility": forms.Select(attrs={"class": "form-select"}),
        }
        help_texts = {
            "rating": "Escoge un valor entre 1 (muy baja utilidad) y 5 (muy útil).",
            "visibility": "Define quién puede ver este comentario dentro del equipo.",
        }

    def clean_comment(self):
        comment = self.cleaned_data.get("comment", "").strip()
        if len(comment) < 10:
            raise forms.ValidationError("Cuéntanos un poco más. Usa al menos 10 caracteres.")
        return comment


class RecruitmentProcessForm(forms.ModelForm):
    class Meta:
        model = RecruitmentProcess
        fields = ("title", "description", "status", "start_date", "end_date")
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej. Senior Backend"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "start_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "end_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        }


class ProcessStageForm(forms.ModelForm):
    class Meta:
        model = ProcessStage
        fields = ("name", "order", "description", "due_date", "is_blocker")
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "order": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "due_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "is_blocker": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_order(self):
        order = self.cleaned_data.get("order")
        if order is None or order < 1:
            raise forms.ValidationError("Define un orden mayor o igual a 1.")
        return order


class CandidateAssignmentForm(forms.ModelForm):
    candidate = forms.ModelChoiceField(
        queryset=get_user_model().objects.all(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = CandidateAssignment
        fields = ("candidate", "current_stage")
        widgets = {
            "current_stage": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        process = kwargs.pop("process", None)
        super().__init__(*args, **kwargs)
        if process:
            self.fields["current_stage"].queryset = process.stages.order_by("order")

    def clean(self):
        cleaned_data = super().clean()
        candidate = cleaned_data.get("candidate")
        process = self.instance.process if self.instance.pk else getattr(self, "process", None)
        if process and candidate:
            exists = CandidateAssignment.objects.filter(process=process, candidate=candidate).exclude(pk=self.instance.pk).exists()
            if exists:
                raise forms.ValidationError("Este candidato ya está asignado al proceso.")
        return cleaned_data
