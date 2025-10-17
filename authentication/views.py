import logging
from typing import Any

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse


LOGGER = logging.getLogger(__name__)


def _is_sso_ready() -> bool:
    config = settings.AZURE_AD_CONFIG
    return config.get("ENABLED") and all(
        config.get(key)
        for key in ("TENANT_ID", "CLIENT_ID", "CLIENT_SECRET")
    )


def _build_msal_app():
    from msal import ConfidentialClientApplication

    config = settings.AZURE_AD_CONFIG
    authority = f"https://login.microsoftonline.com/{config['TENANT_ID']}"
    return ConfidentialClientApplication(
        client_id=config["CLIENT_ID"],
        client_credential=config["CLIENT_SECRET"],
        authority=authority,
    )


def login_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("blog:dashboard")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("blog:dashboard")
    else:
        form = AuthenticationForm()

    for field in form.fields.values():
        css_class = field.widget.attrs.get("class", "")
        classes = css_class.split()
        if "form-control" not in classes:
            classes.insert(0, "form-control")
        field.widget.attrs["class"] = " ".join(classes).strip()

    context = {
        "form": form,
        "sso_enabled": _is_sso_ready(),
    }
    return render(request, "authentication/login.html", context)


def logout_view(request: HttpRequest) -> HttpResponseRedirect:
    logout(request)
    messages.success(request, "Has cerrado sesión exitosamente.")
    return redirect("/")


def sso_login(request: HttpRequest) -> HttpResponse:
    if not _is_sso_ready():
        messages.error(request, "El inicio de sesión corporativo no está configurado.")
        return redirect("authentication:login")

    config = settings.AZURE_AD_CONFIG
    msal_app = _build_msal_app()
    redirect_uri = request.build_absolute_uri(reverse("authentication:sso_callback"))
    auth_flow = msal_app.initiate_auth_code_flow(
        scopes=config.get("SCOPES", ["User.Read"]),
        redirect_uri=redirect_uri,
    )
    request.session["azure_auth_flow"] = auth_flow
    return redirect(auth_flow["auth_uri"])


def sso_callback(request: HttpRequest) -> HttpResponse:
    flow: dict[str, Any] | None = request.session.pop("azure_auth_flow", None)
    if not flow:
        messages.error(request, "La sesión corporativa expiró, intenta nuevamente.")
        return redirect("authentication:login")

    try:
        msal_app = _build_msal_app()
        result = msal_app.acquire_token_by_auth_code_flow(flow, request.GET)
    except ValueError as exc:
        LOGGER.exception("Error al completar el flujo SSO: %%s", exc)
        messages.error(request, "No se pudo completar el inicio de sesión corporativo.")
        return redirect("authentication:login")

    if "error" in result:
        LOGGER.warning(
            "Azure AD devolvió error: %s - %s",
            result.get("error"),
            result.get("error_description"),
        )
        messages.error(request, "La autenticación corporativa falló.")
        return redirect("authentication:login")

    claims = result.get("id_token_claims", {})
    email = claims.get("preferred_username") or claims.get("email")
    if not email:
        messages.error(request, "No se pudo obtener el correo corporativo.")
        return redirect("authentication:login")

    allowed_domains = settings.AZURE_AD_CONFIG.get("ALLOWED_DOMAINS") or []
    domain = email.split("@")[-1].lower()
    if allowed_domains and domain not in allowed_domains:
        messages.error(request, "Tu dominio corporativo no tiene acceso a la plataforma.")
        return redirect("authentication:login")

    user_model = get_user_model()
    user = user_model.objects.filter(email__iexact=email).first()
    if not user:
        user = user_model.objects.filter(username__iexact=email).first()

    if user and not user.is_active:
        messages.error(request, "Tu usuario está inactivo. Contacta a soporte.")
        return redirect("authentication:login")

    if not user:
        base_username = email.split("@")[0]
        username_candidate = base_username
        suffix = 1
        while user_model.objects.filter(username=username_candidate).exists():
            username_candidate = f"{base_username}{suffix}"
            suffix += 1

        user = user_model(
            username=username_candidate,
            email=email,
        )
        user.set_unusable_password()

    first_name = claims.get("given_name") or ""
    last_name = claims.get("family_name") or ""
    if first_name:
        user.first_name = first_name
    if last_name:
        user.last_name = last_name
    user.save()

    login(request, user)
    request.session["azure_access_token"] = result.get("access_token")
    messages.success(request, "Sesión corporativa iniciada correctamente.")
    return redirect("blog:dashboard")
