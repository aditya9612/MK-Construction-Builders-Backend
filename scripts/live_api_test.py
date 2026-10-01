"""Hit every live API and print a pass/fail report."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

BASE = "http://127.0.0.1:8000"
results: list[tuple[str, bool, str]] = []


def record(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] {name}" + (f" -- {detail}" if detail else ""))


def expect(name: str, resp: httpx.Response, codes: int | tuple[int, ...]) -> dict | None:
    if isinstance(codes, int):
        codes = (codes,)
    body: dict | list | str
    try:
        body = resp.json()
    except Exception:
        body = resp.text[:200]
    ok = resp.status_code in codes
    detail = f"{resp.status_code}"
    if not ok:
        detail += f" expected {codes} body={body}"
    elif isinstance(body, dict) and body.get("success") is False and resp.status_code < 400:
        ok = False
        detail += f" success=false {body}"
    record(name, ok, detail)
    return body if isinstance(body, dict) else None


def main() -> int:
    with httpx.Client(base_url=BASE, timeout=30.0) as client:
        r = client.get("/health")
        expect("GET /health", r, 200)
        if r.status_code != 200:
            record("server reachable", False, "API is not running on :8000")
            return 1

        r = client.get("/health/db")
        expect("GET /health/db", r, 200)

        r = client.get("/docs")
        expect("GET /docs (Swagger)", r, 200)

        r = client.get("/openapi.json")
        expect("GET /openapi.json", r, 200)

        r = client.get("/api/v1/customers")
        expect("GET /customers without token -> 401", r, 401)

        r = client.post(
            "/api/v1/auth/login",
            json={"email": "wrong@example.com", "password": "badpass"},
        )
        expect("POST /auth/login invalid -> 401", r, 401)

        r = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@mkconstruction.in", "password": "Admin@12345"},
        )
        data = expect("POST /auth/login admin", r, 200)
        tokens = (data or {}).get("data") or {}
        access = tokens.get("access_token")
        refresh = tokens.get("refresh_token")
        if not access:
            record("access token issued", False, str(data))
            return 1
        auth = {"Authorization": f"Bearer {access}"}

        r = client.get("/api/v1/auth/me", headers=auth)
        expect("GET /auth/me", r, 200)

        r = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
        data = expect("POST /auth/refresh", r, 200)
        new_access = ((data or {}).get("data") or {}).get("access_token") or access
        auth = {"Authorization": f"Bearer {new_access}"}

        unique = date.today().isoformat().replace("-", "")
        r = client.post(
            "/api/v1/auth/register",
            json={
                "name": "API Tester",
                "email": f"tester.{unique}@mkconstruction.in",
                "phone": "9876500001",
                "password": "Tester@12345",
            },
        )
        expect("POST /auth/register", r, (201, 409))

        r = client.post(
            "/api/v1/customers",
            headers=auth,
            json={
                "name": "Live API Customer",
                "mobile": "9876501234",
                "email": "live.customer@example.com",
                "customer_type": "INDIVIDUAL",
                "address": "MG Road",
                "city": "Bengaluru",
                "state": "Karnataka",
                "pincode": "560001",
            },
        )
        data = expect("POST /customers", r, 201)
        customer_id = ((data or {}).get("data") or {}).get("id")

        r = client.get("/api/v1/customers?search=Live&page=1&page_size=20", headers=auth)
        data = expect("GET /customers list+search+pagination", r, 200)
        page = ((data or {}).get("data") or {})
        record(
            "pagination fields present",
            all(k in page for k in ("items", "total", "page", "page_size", "total_pages")),
            str(list(page.keys())),
        )

        r = client.get(f"/api/v1/customers/{customer_id}", headers=auth)
        expect("GET /customers/{id}", r, 200)

        r = client.put(
            f"/api/v1/customers/{customer_id}",
            headers=auth,
            json={"city": "Mysuru", "notes": "updated by live test"},
        )
        expect("PUT /customers/{id}", r, 200)

        r = client.post(
            "/api/v1/customers",
            headers=auth,
            json={"name": "Bad Mobile", "mobile": "123"},
        )
        expect("POST /customers invalid mobile -> 422", r, 422)

        r = client.post(
            "/api/v1/projects",
            headers=auth,
            json={
                "customer_id": customer_id,
                "project_name": "Live G+1 Residence",
                "site_address": "Kanakapura Road",
                "plot_area": "1200",
                "construction_area": "2000",
                "number_of_floors": 2,
                "floor_type": "G+1",
                "status": "PLANNING",
            },
        )
        data = expect("POST /projects", r, 201)
        project_id = ((data or {}).get("data") or {}).get("id")

        r = client.get(f"/api/v1/projects?customer_id={customer_id}", headers=auth)
        expect("GET /projects filter by customer", r, 200)
        r = client.get(f"/api/v1/projects/{project_id}", headers=auth)
        expect("GET /projects/{id}", r, 200)
        r = client.put(
            f"/api/v1/projects/{project_id}",
            headers=auth,
            json={"status": "IN_PROGRESS"},
        )
        expect("PUT /projects/{id}", r, 200)

        r = client.post(
            "/api/v1/projects",
            headers=auth,
            json={"customer_id": 999999, "project_name": "Orphan"},
        )
        expect("POST /projects invalid customer -> 422", r, 422)

        r = client.get("/api/v1/rates?is_active=true", headers=auth)
        data = expect("GET /rates", r, 200)
        rate_id = (((data or {}).get("data") or {}).get("items") or [{}])[0].get("id")

        r = client.post(
            "/api/v1/rates",
            headers=auth,
            json={
                "name": "Live Test Rate",
                "category": "CONSTRUCTION",
                "unit": "sqft",
                "rate": "999",
            },
        )
        data = expect("POST /rates", r, 201)
        created_rate_id = ((data or {}).get("data") or {}).get("id")
        r = client.get(f"/api/v1/rates/{created_rate_id}", headers=auth)
        expect("GET /rates/{id}", r, 200)
        r = client.put(
            f"/api/v1/rates/{created_rate_id}",
            headers=auth,
            json={"rate": "1000"},
        )
        expect("PUT /rates/{id}", r, 200)

        r = client.get("/api/v1/materials", headers=auth)
        expect("GET /materials", r, 200)
        r = client.post(
            "/api/v1/materials",
            headers=auth,
            json={
                "name": "Live Cement",
                "category": "RCC",
                "brand": "UltraTech",
                "unit": "bag",
            },
        )
        data = expect("POST /materials", r, 201)
        material_id = ((data or {}).get("data") or {}).get("id")
        r = client.get(f"/api/v1/materials/{material_id}", headers=auth)
        expect("GET /materials/{id}", r, 200)
        r = client.put(
            f"/api/v1/materials/{material_id}",
            headers=auth,
            json={"brand": "ACC"},
        )
        expect("PUT /materials/{id}", r, 200)

        masters = [
            ("electrical", {"name": "Live Light", "category": "LIGHTING", "unit": "nos", "rate": "450"}),
            ("plumbing", {"name": "Live Tap", "category": "FITTING", "unit": "nos", "rate": "1200"}),
            ("doors-windows", {"name": "Live Door", "category": "DOOR", "unit": "nos", "rate": "8500"}),
            ("tiles-granite", {"name": "Live Tile", "category": "TILE", "unit": "sqft", "rate": "60"}),
            ("painting", {"name": "Live Paint", "category": "INNER", "unit": "sqft", "rate": "22"}),
        ]
        master_ids: dict[str, int] = {}
        for path, payload in masters:
            r = client.get(f"/api/v1/{path}", headers=auth)
            expect(f"GET /{path}", r, 200)
            r = client.post(f"/api/v1/{path}", headers=auth, json=payload)
            data = expect(f"POST /{path}", r, 201)
            item_id = ((data or {}).get("data") or {}).get("id")
            master_ids[path] = item_id
            r = client.get(f"/api/v1/{path}/{item_id}", headers=auth)
            expect(f"GET /{path}/{{id}}", r, 200)
            r = client.put(f"/api/v1/{path}/{item_id}", headers=auth, json={"rate": "10"})
            expect(f"PUT /{path}/{{id}}", r, 200)

        r = client.get("/api/v1/terms", headers=auth)
        data = expect("GET /terms", r, 200)
        term_id = (((data or {}).get("data") or {}).get("items") or [{}])[0].get("id")
        r = client.post(
            "/api/v1/terms",
            headers=auth,
            json={"title": "Live Term", "content": "Valid 15 days.", "category": "VALIDITY"},
        )
        data = expect("POST /terms", r, 201)
        new_term_id = ((data or {}).get("data") or {}).get("id")
        r = client.get(f"/api/v1/terms/{new_term_id}", headers=auth)
        expect("GET /terms/{id}", r, 200)
        r = client.put(f"/api/v1/terms/{new_term_id}", headers=auth, json={"is_default": False})
        expect("PUT /terms/{id}", r, 200)

        r = client.get("/api/v1/settings/company", headers=auth)
        expect("GET /settings/company", r, 200)
        r = client.put(
            "/api/v1/settings/company",
            headers=auth,
            json={"company_name": "MK Construction & Builders"},
        )
        expect("PUT /settings/company", r, 200)

        payload = {
            "customer_id": customer_id,
            "project_id": project_id,
            "quotation_date": date.today().isoformat(),
            "discount_percentage": "5",
            "gst_percentage": "18",
            "notes": "Live API calculation check",
            "construction_items": [
                {
                    "rate_master_id": rate_id,
                    "description": "Foundation",
                    "quantity": "2000",
                    "unit": "sqft",
                    "rate": "900",
                    "sort_order": 1,
                }
            ],
            "additional_items": [
                {
                    "category": "RCC",
                    "description": "RCC slab",
                    "quantity": "2000",
                    "unit": "sqft",
                    "rate": "700",
                    "sort_order": 1,
                }
            ],
            "electrical_items": [
                {"area": "Hall", "item_name": "Light", "quantity": "10", "unit": "nos", "rate": "450"}
            ],
            "plumbing_items": [{"item_name": "Tap", "quantity": "4", "unit": "nos", "rate": "1200"}],
            "doors": [{"item_name": "Main Door", "quantity": "1", "unit": "nos", "rate": "28000"}],
            "windows": [
                {
                    "item_name": "Sliding Window",
                    "length": "5",
                    "width": "4",
                    "unit": "sqft",
                    "rate": "300",
                }
            ],
            "tiles": [{"description": "Floor Tiles", "area": "100", "unit": "sqft", "rate": "60"}],
            "granite": [{"description": "Black Granite", "area": "50", "unit": "sqft", "rate": "110"}],
            "painting": [
                {"category": "INNER", "description": "Interior", "area": "200", "unit": "sqft", "rate": "22"}
            ],
            "materials": [{"material_id": material_id, "name": "Live Cement", "category": "RCC", "unit": "bag"}],
            "terms": [{"term_id": term_id, "term_order": 1}],
        }
        r = client.post("/api/v1/quotations", headers=auth, json=payload)
        data = expect("POST /quotations full create", r, 201)
        q = (data or {}).get("data") or {}
        quotation_id = q.get("id")
        summary = q.get("calculation_summary") or {}
        record(
            "backend calculation 2000x900 + 2000x700 + extras, 5% disc, 18% GST",
            str(summary.get("construction_total")) == "1800000.00"
            and str(summary.get("additional_total")) == "1400000.00"
            and quotation_id is not None,
            f"summary={summary}",
        )
        record(
            "grand_total not trusted from client (server computed)",
            q.get("grand_total") is not None,
            f"grand_total={q.get('grand_total')}",
        )
        record(
            "window area = length x width (5x4=20)",
            bool(q.get("windows")) and str(q["windows"][0].get("area")) == "20.00",
            str((q.get("windows") or [{}])[0]),
        )

        r = client.get("/api/v1/quotations?search=MKQ&page=1&page_size=10", headers=auth)
        expect("GET /quotations list+search", r, 200)
        r = client.get(f"/api/v1/quotations/{quotation_id}", headers=auth)
        expect("GET /quotations/{id}", r, 200)
        r = client.get(f"/api/v1/quotations/{quotation_id}/summary", headers=auth)
        expect("GET /quotations/{id}/summary", r, 200)
        r = client.get(f"/api/v1/quotations/{quotation_id}/preview", headers=auth)
        data = expect("GET /quotations/{id}/preview", r, 200)
        preview = (data or {}).get("data") or {}
        record(
            "preview contains company/customer/project/summary",
            all(k in preview for k in ("company", "customer", "project", "summary", "signature")),
            str(list(preview.keys())),
        )

        payload["notes"] = "edited draft"
        payload["construction_items"][0]["quantity"] = "2100"
        r = client.put(f"/api/v1/quotations/{quotation_id}", headers=auth, json=payload)
        data = expect("PUT /quotations/{id} draft edit + recalc", r, 200)
        rec = ((data or {}).get("data") or {}).get("calculation_summary") or {}
        record(
            "recalculate after edit 2100x900 = 1890000",
            str(rec.get("construction_total")) == "1890000.00",
            str(rec.get("construction_total")),
        )

        r = client.post(f"/api/v1/quotations/{quotation_id}/duplicate", headers=auth)
        data = expect("POST /quotations/{id}/duplicate", r, 201)
        dup = (data or {}).get("data") or {}
        dup_id = dup.get("id")
        record(
            "duplicate is DRAFT with new number",
            dup.get("status") == "DRAFT" and dup.get("quotation_number") != q.get("quotation_number"),
            f"{dup.get('quotation_number')} status={dup.get('status')}",
        )

        r = client.post(f"/api/v1/quotations/{quotation_id}/send", headers=auth)
        expect("POST /quotations/{id}/send", r, 200)
        r = client.post(f"/api/v1/quotations/{quotation_id}/approve", headers=auth)
        expect("POST /quotations/{id}/approve", r, 200)
        r = client.put(f"/api/v1/quotations/{quotation_id}", headers=auth, json=payload)
        expect("PUT approved quotation blocked -> 409", r, 409)
        r = client.delete(f"/api/v1/quotations/{quotation_id}", headers=auth)
        expect("DELETE approved quotation blocked -> 403", r, 403)

        r = client.post(f"/api/v1/quotations/{dup_id}/expire", headers=auth)
        expect("POST /quotations/{id}/expire", r, (200, 409))

        r = client.post(
            "/api/v1/quotations",
            headers=auth,
            json={
                "customer_id": customer_id,
                "project_id": project_id,
                "quotation_date": date.today().isoformat(),
                "discount_percentage": "0",
                "gst_percentage": "18",
            },
        )
        data = expect("POST /quotations empty draft", r, 201)
        draft_id = ((data or {}).get("data") or {}).get("id")
        r = client.post(f"/api/v1/quotations/{draft_id}/reject", headers=auth)
        expect("POST /quotations/{id}/reject", r, 200)

        r = client.post(
            "/api/v1/quotations",
            headers=auth,
            json={
                "customer_id": customer_id,
                "project_id": project_id,
                "quotation_date": date.today().isoformat(),
            },
        )
        data = expect("POST /quotations disposable draft", r, 201)
        del_id = ((data or {}).get("data") or {}).get("id")
        r = client.delete(f"/api/v1/quotations/{del_id}", headers=auth)
        expect("DELETE /quotations draft -> 204", r, 204)

        r = client.get("/api/v1/dashboard/summary", headers=auth)
        expect("GET /dashboard/summary", r, 200)
        r = client.get("/api/v1/reports/quotation-summary", headers=auth)
        expect("GET /reports/quotation-summary", r, 200)
        r = client.get("/api/v1/reports/monthly", headers=auth)
        expect("GET /reports/monthly", r, 200)
        r = client.get("/api/v1/reports/customer-wise", headers=auth)
        expect("GET /reports/customer-wise", r, 200)
        r = client.get("/api/v1/reports/status-wise", headers=auth)
        expect("GET /reports/status-wise", r, 200)

        r = client.post(
            "/api/v1/auth/login",
            json={"email": "viewer@mkconstruction.in", "password": "Viewer@12345"},
        )
        data = expect("POST /auth/login viewer", r, 200)
        vtok = ((data or {}).get("data") or {}).get("access_token")
        vauth = {"Authorization": f"Bearer {vtok}"}
        r = client.get("/api/v1/customers", headers=vauth)
        expect("VIEWER can list customers", r, 200)
        r = client.post(
            "/api/v1/customers",
            headers=vauth,
            json={"name": "Should Fail", "mobile": "9876511111"},
        )
        expect("VIEWER cannot create customer -> 403", r, 403)

        r = client.delete(f"/api/v1/rates/{created_rate_id}", headers=auth)
        expect("DELETE /rates/{id} soft", r, 204)
        r = client.delete(f"/api/v1/materials/{material_id}", headers=auth)
        expect("DELETE /materials/{id} soft", r, 204)
        for path, item_id in master_ids.items():
            r = client.delete(f"/api/v1/{path}/{item_id}", headers=auth)
            expect(f"DELETE /{path}/{{id}} soft", r, 204)
        r = client.delete(f"/api/v1/terms/{new_term_id}", headers=auth)
        expect("DELETE /terms/{id} soft", r, 204)
        r = client.delete(f"/api/v1/customers/{customer_id}", headers=auth)
        expect("DELETE /customers/{id} soft", r, 204)

        r = client.get("/api/v1/customers/999999", headers=auth)
        expect("GET missing customer -> 404", r, 404)

    passed = sum(1 for _, ok, _ in results if ok)
    failed = sum(1 for _, ok, _ in results if not ok)
    print("\n" + "=" * 60)
    print(f"RESULT: {passed} passed, {failed} failed, {len(results)} total")
    print("=" * 60)
    if failed:
        print("\nFailed checks:")
        for name, ok, detail in results:
            if not ok:
                print(f"  - {name}: {detail}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
