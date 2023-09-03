from cli_test_helpers import shell

RESOURCE_DIR = "resource-examples"


class TestCreateRemove:
    def test_compute_source(self):
        resources = f"{RESOURCE_DIR}/compute-sources.json"
        result = shell(f"yd-create {resources}")
        assert result.exit_code == 0
        result = shell(f"yd-remove -y {resources}")
        assert result.exit_code == 0

    def test_compute_template(self):
        resources = f"{RESOURCE_DIR}/compute-template.json"
        result = shell(f"yd-create {resources}")
        assert result.exit_code == 0
        result = shell(f"yd-remove -y {resources}")
        assert result.exit_code == 0

    def test_configured_worker_pool(self):
        resources = f"{RESOURCE_DIR}/configured-worker-pool.json"
        result = shell(f"yd-create {resources}")
        assert result.exit_code == 0
        result = shell(f"yd-remove -y {resources}")
        assert result.exit_code == 0

    def test_image_family(self):
        resources = f"{RESOURCE_DIR}/image-family.json"
        result = shell(f"yd-create {resources}")
        assert result.exit_code == 0
        result = shell(f"yd-remove -y {resources}")
        assert result.exit_code == 0

    def test_keyring_and_credential(self):
        resources = f"{RESOURCE_DIR}/keyring.json {RESOURCE_DIR}/credential.json"
        result = shell(f"yd-create {resources}")
        assert result.exit_code == 0
        resources = f"{RESOURCE_DIR}/credential.json {RESOURCE_DIR}/keyring.json"
        result = shell(f"yd-remove -y {resources}")
        assert result.exit_code == 0

    def test_namespace(self):
        resources = f"{RESOURCE_DIR}/namespace.json"
        result = shell(f"yd-create {resources}")
        assert result.exit_code == 0
        result = shell(f"yd-remove -y {resources}")
        assert result.exit_code == 0
