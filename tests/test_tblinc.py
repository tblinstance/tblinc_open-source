"""Comprehensive end-to-end test suite for tblinc AI Models, Web Framework, Generator, and CLI."""

from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

from tblinc_open_source.ai_models import (
    AdamWOptimizer,
    BPETokenizer,
    ModelRegistry,
    MultiHeadSelfAttention,
    Tensor,
    TransformerBlock,
    active_compute_backend,
    installed_backends,
    list_models,
    registry,
    system_report,
    verify_all_models,
)
from tblinc_open_source.cli import main as cli_main
from tblinc_open_source.generator import create_ai_project
from tblinc_open_source.web.admin.quota import (
    ensure_user_wallet,
    provision_default_user_key,
)
from tblinc_open_source.web.auth.service import (
    authenticate,
    create_superuser,
    create_user,
)


class TblincFullProjectTests(unittest.TestCase):
    def test_25_ai_models_and_legacy_aliases(self) -> None:
        specs = list_models()
        self.assertEqual(len(specs), 25)
        canonical_keys = {spec["key"] for spec in specs}
        self.assertEqual(
            canonical_keys,
            {
                "audio",
                "boost",
                "chat",
                "classify",
                "cluster",
                "detector",
                "embed",
                "forecast",
                "forest",
                "image",
                "multimodal",
                "music",
                "neural",
                "objects",
                "predict",
                "recommend",
                "search",
                "sentiment",
                "similarity",
                "summarize",
                "transcribe",
                "tree",
                "video",
                "vision",
                "voice",
            },
        )
        # Verify legacy aliases resolve cleanly
        for alias, target in [
            ("llm", "chat"),
            ("ddpm", "image"),
            ("tts", "voice"),
            ("asr", "transcribe"),
            ("yolo", "objects"),
            ("xgboost", "boost"),
            ("cart", "tree"),
            ("kmeans", "cluster"),
        ]:
            self.assertEqual(registry.create(alias).metadata.key, target)

        # Verify hardware summary includes tensorflow and cuda stack detectors
        backends = installed_backends()
        self.assertIn("tensorflow", backends)
        self.assertIn("jax", backends)
        report = system_report()
        self.assertIn("hardware", report)
        self.assertIn("preferred_device", report["hardware"])

        # Verify core neural engine primitives (Tensor, BPETokenizer, MultiHeadSelfAttention, TransformerBlock, AdamW)
        self.assertIn(":", active_compute_backend())
        tok = BPETokenizer(vocab_size=64).fit(["transformers learn self attention representations"])
        encoded = tok.encode("transformers learn attention")
        self.assertGreaterEqual(len(encoded), 3)
        self.assertIn("transformers", tok.decode(encoded))

        block = TransformerBlock(embed_dim=16, num_heads=4)
        out_seq, attn_w = block.forward([[0.1] * 16, [0.2] * 16, [0.3] * 16], causal=True)
        self.assertEqual(len(out_seq), 3)
        self.assertEqual(len(out_seq[0]), 16)
        self.assertEqual(len(attn_w[-1]), 3)

        # Full round-trip train + predict + save + load across all 25 models
        ver = verify_all_models()
        self.assertTrue(ver["all_ok"], f"Model verification failed: {ver}")
        self.assertEqual(ver["passed"], 25)

    def test_cli_commands(self) -> None:
        self.assertEqual(cli_main(["info"]), 0)
        self.assertEqual(cli_main(["devices"]), 0)
        self.assertEqual(cli_main(["models", "list"]), 0)
        self.assertEqual(cli_main(["models", "listt"]), 0)
        self.assertEqual(cli_main(["models", "tblincv1", "multimodal"]), 0)
        self.assertEqual(cli_main(["verify"]), 0)
        self.assertEqual(cli_main(["install", "--dry-run", "all"]), 0)

    def test_generator_and_web_platform_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = create_ai_project("ai_test_proj", destination=Path(tmp))
            self.assertTrue((project_dir / "app.py").exists())
            self.assertTrue((project_dir / "templates" / "layouts" / "base.html").exists())

            sys.path.insert(0, str(project_dir))
            try:
                import importlib

                app_mod = importlib.import_module("app")
                app = app_mod.create_app(database_path=project_dir / "test.sqlite3")
                client = app.test_client()

                # 1. Public pages & APIs (/models/ is staff-protected and redirects to /admin/login/)
                for path in [
                    "/",
                    "/auth/login/",
                    "/auth/register/",
                    "/experiments/",
                    "/api/experiments/",
                    "/api/datasets/",
                    "/api/system/",
                ]:
                    res = client.get(path)
                    self.assertEqual(res.status, 200, f"GET {path} failed with {res.status}")
                self.assertEqual(client.get("/models/").status, 302)

                sys_payload = json.loads(client.get("/api/system/").text)
                self.assertEqual(sys_payload["ai_model_count"], 25)

                # 2. User registration, starter key, $10 credit, and authenticated profile/billing/settings
                user = create_user("alice", "StrongPass123!", email="alice@example.com")
                self.assertIsNotNone(user)
                key_obj = provision_default_user_key("alice")
                self.assertIsNotNone(key_obj)
                self.assertTrue(key_obj.api_key.startswith("tbl_sk_"))
                ensure_user_wallet("alice")

                # Log in via session cookie
                login_page = client.get("/auth/login/")
                m_csrf = re.search(r'name="csrf_token"\s+value="([^"]+)"', login_page.text)
                self.assertIsNotNone(m_csrf)
                csrf = m_csrf.group(1)
                login_res = client.post(
                    "/auth/login/",
                    data={"username": "alice", "password": "StrongPass123!", "csrf_token": csrf},
                )
                self.assertIn(login_res.status, (200, 302))

                for path in ["/profile/", "/billing/", "/settings/", "/api/user/keys", "/api/user/billing"]:
                    res = client.get(path)
                    self.assertEqual(res.status, 200, f"Authenticated GET {path} failed with {res.status}")

                # 3. Create additional personal AI key and top up billing balance
                key_res = client.post("/api/user/keys", json_body={"name": "Alice CLI Key"})
                self.assertEqual(key_res.status, 201)
                key_data = json.loads(key_res.text)
                self.assertTrue(key_data["key"]["api_key"].startswith("tbl_sk_"))

                topup_res = client.post("/api/user/billing/topup", json_body={"amount_usd": 25.0})
                self.assertEqual(topup_res.status, 201)
                topup_data = json.loads(topup_res.text)
                self.assertGreaterEqual(float(topup_data["balance_usd"]), 25.0)

                # 4. Superuser Admin dashboard + dynamic User dropdown on BillingTransaction form
                admin_user = create_superuser("rootadmin", "AdminSecret123!", "root@example.com")
                self.assertIsNotNone(admin_user)
                self.assertIsNotNone(authenticate("rootadmin", "AdminSecret123!"))

                admin_client = app.test_client()
                admin_login_page = admin_client.get("/admin/login/")
                m_admin_csrf = re.search(r'name="csrf_token"\s+value="([^"]+)"', admin_login_page.text)
                self.assertIsNotNone(m_admin_csrf)
                admin_csrf = m_admin_csrf.group(1)
                admin_login = admin_client.post(
                    "/admin/login/",
                    data={
                        "username": "rootadmin",
                        "password": "AdminSecret123!",
                        "csrf_token": admin_csrf,
                    },
                )
                self.assertIn(admin_login.status, (200, 302))

                for path in [
                    "/admin/",
                    "/admin/ai/",
                    "/admin/models/",
                    "/admin/train/",
                    "/admin/keys/",
                    "/admin/settings/",
                    "/admin/billingtransaction/create/",
                    "/admin/aikey/create/",
                ]:
                    res = admin_client.get(path)
                    self.assertEqual(res.status, 200, f"Admin GET {path} failed with {res.status}")
                    if path == "/admin/billingtransaction/create/":
                        html = res.text
                        self.assertIn("<select", html)
                        self.assertIn("alice", html)
                        self.assertIn("rootadmin", html)

                # 5. Train a custom model checkpoint via /api/ai/train and verify live AI endpoints load it
                train_res = admin_client.post(
                    "/api/ai/train",
                    json_body={
                        "model_key": "chat",
                        "run_name": "Custom Transformer Checkpoint",
                        "hyperparams": {"context_window": 4, "embed_dim": 16, "epochs": 2},
                        "dataset": {
                            "corpus": [
                                "custom quantum neural engine -> The custom quantum neural engine accelerates deep learning!",
                            ]
                        },
                    },
                )
                self.assertEqual(train_res.status, 201)

                chat_res = admin_client.post("/api/ai/chat", json_body={"message": "What is 15 * 4?"})
                self.assertEqual(chat_res.status, 200)
                chat_data = json.loads(chat_res.text)
                self.assertIn("60", chat_data["reply"])
                self.assertIn("checkpoint:", chat_data["source"])

                admin_guide_res = admin_client.post(
                    "/api/ai/chat",
                    json_body={"message": "How does tblinc generate an admin panel?"},
                )
                self.assertEqual(admin_guide_res.status, 200)
                admin_guide_data = json.loads(admin_guide_res.text)
                self.assertIn("AdminSite", admin_guide_data["reply"])

                for ep, body in [
                    ("/api/ai/image", {"prompt": "robot", "style": "neon", "steps": 8}),
                    ("/api/ai/video", {"prompt": "neon wave", "motion": "orbit", "frames": 12}),
                    ("/api/ai/audio", {"text": "Hello tblinc AI", "voice": "studio"}),
                    ("/api/ai/music", {"mood": "synthwave", "bpm": 112, "duration_sec": 2.0}),
                ]:
                    r_ai = admin_client.post(ep, json_body=body)
                    self.assertEqual(r_ai.status, 200, f"POST {ep} failed with {r_ai.status}")
            finally:
                if str(project_dir) in sys.path:
                    sys.path.remove(str(project_dir))


if __name__ == "__main__":
    unittest.main()
