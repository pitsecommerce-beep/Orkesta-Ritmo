import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

BOVEDA_FORBIDDEN_PATTERNS = [
    b".key", b".cer", b"BEGIN PRIVATE KEY",
    b"BEGIN CERTIFICATE", b"PKCS", b"X509",
]


class TestNoRouteExposesBoveda:
    def test_no_route_returns_vault_material(self):
        routes = []
        for route in app.routes:
            if hasattr(route, "path"):
                routes.append(route.path)

        for path in routes:
            if "{" in path:
                test_path = path.replace("{tenant_id}", "test-tenant")
                test_path = test_path.replace("{periodo_id}", "test-periodo")
                test_path = test_path.replace("{cfdi_id}", "test-cfdi")
                test_path = test_path.replace("{documento_id}", "test-doc")
                test_path = test_path.replace("{extracto_id}", "test-ext")
                test_path = test_path.replace("{actividad_id}", "test-act")
                test_path = test_path.replace("{nodo_id}", "test-nodo")
                test_path = test_path.replace("{id}", "test-id")
            else:
                test_path = path

            for method in ["GET"]:
                response = client.get(test_path)
                if response.status_code == 200:
                    body = response.content
                    for pattern in BOVEDA_FORBIDDEN_PATTERNS:
                        assert pattern not in body, (
                            f"Route {method} {test_path} may expose vault material "
                            f"(found pattern: {pattern})"
                        )

    def test_boveda_upload_blocked_without_feature_flag(self):
        response = client.post(
            "/api/boveda/upload",
            params={
                "password": "test",
                "tenant_id": "test",
                "consentimiento_hash": "abc123",
            },
            files={
                "cer": ("test.cer", b"fake cer content"),
                "key": ("test.key", b"fake key content"),
            },
        )
        assert response.status_code == 403
        body = response.json()
        assert "no está habilitada" in body["detail"]

    def test_boveda_delete_blocked_without_feature_flag(self):
        response = client.delete("/api/boveda/test-tenant")
        assert response.status_code == 403

    def test_boveda_bitacora_blocked_without_feature_flag(self):
        response = client.get("/api/boveda/test-tenant/bitacora")
        assert response.status_code == 403


class TestBovedaCrypto:
    def test_encrypt_decrypt_roundtrip(self):
        from app.services.boveda import (
            generate_data_key,
            encrypt_with_master_key,
            decrypt_with_master_key,
            encrypt_file,
            decrypt_file,
        )
        import secrets

        master_key = secrets.token_hex(32)
        data_key = generate_data_key()

        encrypted_dk = encrypt_with_master_key(data_key, master_key)
        decrypted_dk = decrypt_with_master_key(encrypted_dk, master_key)
        assert decrypted_dk == data_key

        content = b"This is a test .key file content"
        encrypted = encrypt_file(content, data_key)
        decrypted = decrypt_file(encrypted, data_key)
        assert decrypted == content

    def test_destroy_data_key(self):
        from app.services.boveda import generate_data_key, encrypt_with_master_key, destroy_data_key
        import secrets

        master_key = secrets.token_hex(32)
        data_key = generate_data_key()
        encrypted_dk = encrypt_with_master_key(data_key, master_key)

        destroyed = destroy_data_key(encrypted_dk)
        assert destroyed == b'\x00' * len(encrypted_dk)
        assert destroyed != encrypted_dk

    def test_wrong_master_key_fails(self):
        from app.services.boveda import (
            generate_data_key,
            encrypt_with_master_key,
            decrypt_with_master_key,
        )
        import secrets

        master_key1 = secrets.token_hex(32)
        master_key2 = secrets.token_hex(32)
        data_key = generate_data_key()

        encrypted = encrypt_with_master_key(data_key, master_key1)
        with pytest.raises(Exception):
            decrypt_with_master_key(encrypted, master_key2)
