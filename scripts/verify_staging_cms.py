"""End-to-end staging verification script for MK Construction CMS and ERP integration."""

import io
import sys
from pathlib import Path
import httpx

BASE_URL = "http://127.0.0.1:8001"

def create_tiny_png() -> bytes:
    # 1x1 transparent PNG
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01"
        b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )

def run_staging_verification():
    print("=== Starting End-to-End Staging Verification ===")
    with httpx.Client(base_url=BASE_URL, timeout=15.0) as client:
        # 1. Health checks
        r = client.get("/health")
        assert r.status_code == 200, f"/health failed: {r.status_code}"
        r = client.get("/health/db")
        assert r.status_code == 200, f"/health/db failed: {r.status_code}"
        print("[PASS] System and DB health endpoints are healthy")

        # 2. ERP Auth Login
        login_res = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@mkconstruction.in", "password": "Admin@12345"},
        )
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        token = login_res.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("[PASS] ERP Auth login successful")

        # 3. ERP Existing Endpoints verification
        r_cust = client.get("/api/v1/customers", headers=headers)
        assert r_cust.status_code == 200, f"GET /customers failed: {r_cust.text}"
        r_proj = client.get("/api/v1/projects", headers=headers)
        assert r_proj.status_code == 200, f"GET /projects failed: {r_proj.text}"
        r_quot = client.get("/api/v1/quotations", headers=headers)
        assert r_quot.status_code == 200, f"GET /quotations failed: {r_quot.text}"
        print("[PASS] Existing ERP endpoints (customers, projects, quotations) functioning normally")

        # Clean up any leftover staging test records from previous runs
        admin_projects = client.get("/api/v1/admin/portfolio/projects", headers=headers).json().get("data", {}).get("items", [])
        for p in admin_projects:
            if "staging" in p.get("slug", ""):
                client.delete(f"/api/v1/admin/portfolio/projects/{p['id']}", headers=headers)
        admin_gal = client.get("/api/v1/admin/gallery", headers=headers).json().get("data", {}).get("items", [])
        for g in admin_gal:
            if g.get("caption") == "Contemporary Facade at Sunset":
                client.delete(f"/api/v1/admin/gallery/{g['id']}", headers=headers)

        # 4. Public CMS endpoints (empty state)
        r_pub_port = client.get("/api/v1/portfolio/projects")
        assert r_pub_port.status_code == 200
        r_pub_gal = client.get("/api/v1/gallery")
        assert r_pub_gal.status_code == 200
        print("[PASS] Public CMS endpoints accessible without authentication")

        # 5. Media Upload
        png_data = create_tiny_png()
        files = {"file": ("test_staging.png", io.BytesIO(png_data), "image/png")}
        r_upload = client.post(
            "/api/v1/admin/upload/image",
            params={"folder": "portfolio"},
            files=files,
            headers=headers,
        )
        assert r_upload.status_code == 201, f"Upload failed: {r_upload.text}"
        media_data = r_upload.json()["data"]
        media_id = media_data["id"]
        media_url = media_data["url_path"]
        print(f"[PASS] Media uploaded successfully: ID={media_id}, path={media_url}, dimensions={media_data.get('width')}x{media_data.get('height')}")

        # 6. Verify Static Serving
        r_static = client.get(media_url)
        assert r_static.status_code == 200, f"Static media fetch failed: {r_static.status_code}"
        assert len(r_static.content) == len(png_data), "Static content byte length mismatch"
        print("[PASS] Static media file served correctly over /media/ route")

        # Upload a second image for gallery
        files2 = {"file": ("test_staging_2.png", io.BytesIO(png_data), "image/png")}
        r_upload2 = client.post(
            "/api/v1/admin/upload/image",
            params={"folder": "gallery"},
            files=files2,
            headers=headers,
        )
        assert r_upload2.status_code == 201
        media2_id = r_upload2.json()["data"]["id"]
        print(f"[PASS] Second media uploaded successfully: ID={media2_id}")

        # 7. Portfolio Project CRUD
        project_payload = {
            "name": "Staging Luxury Villa",
            "slug": "staging-luxury-villa",
            "location": "Banjara Hills, Hyderabad",
            "type": "RESIDENTIAL",
            "status": "IN_PROGRESS",
            "main_image_id": media_id,
            "description": "Premium 5-bedroom villa with sustainable solar integration.",
            "overview": "Complete structural and architectural design.",
            "work_progress": "Foundation and ground floor slab casting complete.",
            "final_result": "Under construction.",
            "publication_status": "DRAFT",
            "display_order": 1,
            "gallery_media_ids": [media2_id],
        }
        r_create_proj = client.post(
            "/api/v1/admin/portfolio/projects",
            json=project_payload,
            headers=headers,
        )
        assert r_create_proj.status_code == 201, f"Create project failed: {r_create_proj.text}"
        project_id = r_create_proj.json()["data"]["id"]
        print(f"[PASS] Portfolio project created: ID={project_id}")

        # Check public list (should NOT include draft project)
        r_pub_list = client.get("/api/v1/portfolio/projects")
        assert len(r_pub_list.json()["data"]["items"]) == 0, "Draft project leaked into public list"
        print("[PASS] Publication boundary verified: draft project is hidden from public API")

        # Publish project
        r_pub_update = client.put(
            f"/api/v1/admin/portfolio/projects/{project_id}",
            json={"publication_status": "PUBLISHED"},
            headers=headers,
        )
        assert r_pub_update.status_code == 200
        print("[PASS] Project updated to published")

        # Now check public list and slug
        r_pub_list_now = client.get("/api/v1/portfolio/projects")
        assert len(r_pub_list_now.json()["data"]["items"]) == 1
        r_slug = client.get("/api/v1/portfolio/projects/staging-luxury-villa")
        assert r_slug.status_code == 200
        proj_detail = r_slug.json()["data"]
        assert proj_detail["name"] == "Staging Luxury Villa"
        assert len(proj_detail["gallery"]) == 1
        print("[PASS] Public project details retrieved by slug with gallery items")

        # 8. Gallery Items CRUD
        gallery_payload = {
            "media_id": media2_id,
            "caption": "Contemporary Facade at Sunset",
            "category": "exterior",
            "object_position": "center",
            "display_order": 1,
            "publication_status": "PUBLISHED",
        }
        r_create_gal = client.post(
            "/api/v1/admin/gallery",
            json=gallery_payload,
            headers=headers,
        )
        assert r_create_gal.status_code == 201, f"Create gallery failed: {r_create_gal.text}"
        gal_item_id = r_create_gal.json()["data"]["id"]
        print(f"[PASS] Gallery item created: ID={gal_item_id}")

        r_gal_pub = client.get("/api/v1/gallery?category=exterior")
        assert r_gal_pub.status_code == 200
        assert len(r_gal_pub.json()["data"]["items"]) == 1
        print("[PASS] Public gallery item retrieved by category filter")

        # 9. Cleanup verification
        # Attempt to delete media referenced by project -> expect 409 conflict
        r_del_fail = client.delete(f"/api/v1/admin/upload/{media_id}", headers=headers)
        assert r_del_fail.status_code == 409, f"Expected 409 when deleting referenced media, got: {r_del_fail.status_code}"
        print("[PASS] Referencing media protected from deletion (409 Conflict)")

        # Clean up gallery item
        r_del_gal = client.delete(f"/api/v1/admin/gallery/{gal_item_id}", headers=headers)
        assert r_del_gal.status_code == 204, f"Delete gallery failed: {r_del_gal.status_code}"
        print("[PASS] Gallery item deleted (204 No Content)")

        # Clean up project
        r_del_proj = client.delete(f"/api/v1/admin/portfolio/projects/{project_id}", headers=headers)
        assert r_del_proj.status_code == 204, f"Delete project failed: {r_del_proj.status_code}"
        print("[PASS] Portfolio project deleted (204 No Content)")

        # Now clean up both media files
        r_del_media1 = client.delete(f"/api/v1/admin/upload/{media_id}", headers=headers)
        assert r_del_media1.status_code == 204, f"Delete media1 failed: {r_del_media1.status_code}"
        r_del_media2 = client.delete(f"/api/v1/admin/upload/{media2_id}", headers=headers)
        assert r_del_media2.status_code == 204, f"Delete media2 failed: {r_del_media2.status_code}"
        print("[PASS] Media files deleted cleanly from DB and disk (204 No Content)")

        # Verify static media route returns 404 now
        r_static_gone = client.get(media_url)
        assert r_static_gone.status_code == 404
        print("[PASS] Deleted media returns 404 on static route")

    print("\nALL STAGING VERIFICATIONS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_staging_verification()
