import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    def test_health(self):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "orkesta-ritmo-api"


class TestAuthEndpoints:
    def test_magic_link(self):
        response = client.post("/api/auth/magic-link", json={"email": "test@example.com"})
        assert response.status_code == 200

    def test_guest_session(self):
        response = client.post("/api/auth/guest-session")
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "expires_at" in data

    def test_guest_set_email(self):
        guest = client.post("/api/auth/guest-session").json()
        response = client.post("/api/auth/guest/set-email", json={
            "guest_token": guest["token"],
            "email": "test@example.com",
        })
        assert response.status_code == 200

    def test_me(self):
        response = client.get("/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data


class TestTenantEndpoints:
    def test_create_tenant_pf(self):
        response = client.post("/api/tenants/", json={
            "rfc": "GARL850101AB1",
            "nombre": "Test PF",
            "regimen": "RESICO_PF",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["tipo_persona"] == "fisica"

    def test_create_tenant_pm(self):
        response = client.post("/api/tenants/", json={
            "rfc": "ORL230101SA3",
            "nombre": "Test PM",
            "regimen": "RESICO_PM",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["tipo_persona"] == "moral"

    def test_create_tenant_invalid_rfc(self):
        response = client.post("/api/tenants/", json={
            "rfc": "INVALID",
            "nombre": "Test",
            "regimen": "RESICO_PF",
        })
        assert response.status_code == 422

    def test_create_tenant_unsupported_regime(self):
        response = client.post("/api/tenants/", json={
            "rfc": "GARL850101AB1",
            "nombre": "Test",
            "regimen": "ACTIVIDAD_EMPRESARIAL",
        })
        assert response.status_code == 422
        data = response.json()
        assert "no soportado" in data["detail"]

    def test_list_tenants(self):
        response = client.get("/api/tenants/")
        assert response.status_code == 200
        assert "tenants" in response.json()


class TestOnboardingEndpoints:
    def test_paso_nombre(self):
        response = client.post("/api/onboarding/paso/nombre", json={"nombre": "María"})
        assert response.status_code == 200
        assert response.json()["siguiente"] == "constancia"

    def test_paso_constancia_sin(self):
        response = client.post("/api/onboarding/paso/constancia", json={"tiene_constancia": False})
        assert response.status_code == 200
        data = response.json()
        assert data["siguiente"] == "guia_constancia"
        assert "guia" in data

    def test_paso_constancia_con(self):
        response = client.post("/api/onboarding/paso/constancia", json={"tiene_constancia": True})
        assert response.status_code == 200
        assert response.json()["siguiente"] == "upload_constancia"

    def test_confirmar_regimen_admitido(self):
        response = client.post("/api/onboarding/paso/confirmar-regimen", json={
            "rfc": "GARL850101AB1",
            "regimen": "RESICO_PF",
            "nombre_constancia": "García López",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["admitido"] is True
        assert data["tipo_persona"] == "fisica"
        assert "tenant_id" in data

    def test_confirmar_regimen_no_admitido(self):
        response = client.post("/api/onboarding/paso/confirmar-regimen", json={
            "rfc": "GARL850101AB1",
            "regimen": "PLATAFORMAS_TECNOLOGICAS",
            "nombre_constancia": "García",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["admitido"] is False
        assert data["lista_espera"] is True


class TestDocumentoEndpoints:
    def test_upload_valid_extension(self):
        response = client.post(
            "/api/documentos/upload",
            params={"tenant_id": "test", "tipo": "xml_cfdi"},
            files={"file": ("test.xml", b"<xml/>", "application/xml")},
        )
        assert response.status_code == 200

    def test_upload_invalid_extension(self):
        response = client.post(
            "/api/documentos/upload",
            params={"tenant_id": "test", "tipo": "xml_cfdi"},
            files={"file": ("test.exe", b"binary", "application/octet-stream")},
        )
        assert response.status_code == 422
        assert "no permitida" in response.json()["detail"]


class TestLegalEndpoints:
    def test_privacidad(self):
        response = client.get("/api/legal/privacidad")
        assert response.status_code == 200
        data = response.json()
        assert data["estado"] == "en_revision"
        assert "Ley Federal" in data["contenido"]

    def test_terminos(self):
        response = client.get("/api/legal/terminos")
        assert response.status_code == 200
        data = response.json()
        assert "No es un despacho contable" in data["contenido"]
        assert "Ritmo prepara" in data["contenido"]


class TestIntencionesEndpoints:
    def test_registrar_intencion(self):
        response = client.post("/api/intenciones/", json={
            "plan": "esencial_mensual",
            "email": "test@example.com",
        })
        assert response.status_code == 200
        assert response.json()["status"] == "registered"

    def test_registrar_intencion_plan_invalido(self):
        response = client.post("/api/intenciones/", json={
            "plan": "inexistente",
        })
        assert response.status_code == 422
        assert "no válido" in response.json()["detail"]


class TestListaEsperaEndpoints:
    def test_registrar_espera(self):
        response = client.post("/api/lista-espera/", json={
            "regimen": "PLATAFORMAS_TECNOLOGICAS",
            "email": "test@example.com",
        })
        assert response.status_code == 200
        assert response.json()["status"] == "registered"


class TestChatEndpoints:
    def test_send_message(self):
        response = client.post(
            "/api/chat/mensaje",
            params={"tenant_id": "test"},
            json={"contenido": "Hola", "canal": "web"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "mensaje_id" in data
        assert data["canal"] == "web"

    def test_send_message_invalid_canal(self):
        response = client.post(
            "/api/chat/mensaje",
            params={"tenant_id": "test"},
            json={"contenido": "Hola", "canal": "telegram"},
        )
        assert response.status_code == 400

    def test_historial(self):
        response = client.get("/api/chat/historial", params={"tenant_id": "test"})
        assert response.status_code == 200
        assert "mensajes" in response.json()


class TestCalculoEndpoints:
    def test_compuertas_no_cfdis(self):
        response = client.get("/api/calculo/compuertas/test-periodo")
        assert response.status_code in (200, 404)
