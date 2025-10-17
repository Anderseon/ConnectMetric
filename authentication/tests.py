from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse


SSO_READY_CONFIG = {
	"ENABLED": True,
	"TENANT_ID": "test-tenant",
	"CLIENT_ID": "client-id",
	"CLIENT_SECRET": "client-secret",
	"SCOPES": ["User.Read"],
	"ALLOWED_DOMAINS": [],
}


class AuthenticationViewsTests(TestCase):
	def test_login_page_renders(self) -> None:
		response = self.client.get(reverse("authentication:login"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Inicia sesión")

	@override_settings(AZURE_AD_CONFIG=SSO_READY_CONFIG)
	@patch("authentication.views._build_msal_app")
	def test_sso_login_redirects_to_authority(self, mock_builder) -> None:
		mock_app = mock_builder.return_value
		mock_app.initiate_auth_code_flow.return_value = {
			"auth_uri": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
			"state": "xyz",
		}

		response = self.client.get(reverse("authentication:sso_login"))

		self.assertEqual(response.status_code, 302)
		self.assertIn("login.microsoftonline.com", response["Location"])
		self.assertIn("azure_auth_flow", self.client.session)

	@override_settings(AZURE_AD_CONFIG=SSO_READY_CONFIG | {"ALLOWED_DOMAINS": ["example.com"]})
	@patch("authentication.views._build_msal_app")
	def test_sso_callback_creates_user_and_logs_in(self, mock_builder) -> None:
		mock_app = mock_builder.return_value
		mock_app.acquire_token_by_auth_code_flow.return_value = {
			"id_token_claims": {
				"preferred_username": "new.user@example.com",
				"given_name": "New",
				"family_name": "User",
			},
			"access_token": "token",
		}

		session = self.client.session
		session["azure_auth_flow"] = {"state": "any"}
		session.save()

		response = self.client.get(
			reverse("authentication:sso_callback"),
			{"code": "123", "state": "any"},
			follow=True,
		)

		self.assertEqual(response.status_code, 200)
		user_model = get_user_model()
		self.assertTrue(user_model.objects.filter(email="new.user@example.com").exists())
		self.assertIn("_auth_user_id", self.client.session)

	@override_settings(AZURE_AD_CONFIG=SSO_READY_CONFIG | {"ALLOWED_DOMAINS": ["example.com"]})
	@patch("authentication.views._build_msal_app")
	def test_sso_callback_rejects_unknown_domain(self, mock_builder) -> None:
		mock_app = mock_builder.return_value
		mock_app.acquire_token_by_auth_code_flow.return_value = {
			"id_token_claims": {
				"preferred_username": "intruder@other.com",
			}
		}

		session = self.client.session
		session["azure_auth_flow"] = {"state": "abc"}
		session.save()

		response = self.client.get(
			reverse("authentication:sso_callback"),
			{"code": "456", "state": "abc"},
			follow=True,
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "dominio corporativo no tiene acceso")
		user_model = get_user_model()
		self.assertFalse(user_model.objects.filter(email="intruder@other.com").exists())
