"""Seed MK Construction & Builders reference data."""

import asyncio
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.company import CompanySettings
from app.models.customer import Customer
from app.models.enums import RoleName
from app.models.masters import (
    DoorWindowMaster,
    ElectricalMaster,
    MaterialMaster,
    PaintingMaster,
    PlumbingMaster,
    RateMaster,
    TileGraniteMaster,
)
from app.models.project import Project
from app.models.term import Term
from app.models.user import Role, User


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        existing = (await session.execute(select(Role))).scalars().first()
        if existing:
            print("Seed data already present. Skipping.")
            return

        roles = {name: Role(name=name) for name in RoleName}
        session.add_all(roles.values())
        await session.flush()

        session.add_all(
            [
                User(
                    name="MK Admin",
                    email="admin@mkconstruction.in",
                    phone="9876543210",
                    password_hash=hash_password("Admin@12345"),
                    role_id=roles[RoleName.ADMIN].id,
                ),
                User(
                    name="Site Manager",
                    email="manager@mkconstruction.in",
                    phone="9876543211",
                    password_hash=hash_password("Manager@12345"),
                    role_id=roles[RoleName.MANAGER].id,
                ),
                User(
                    name="Estimator",
                    email="estimator@mkconstruction.in",
                    phone="9876543212",
                    password_hash=hash_password("Estimator@12345"),
                    role_id=roles[RoleName.ESTIMATOR].id,
                ),
                User(
                    name="Viewer",
                    email="viewer@mkconstruction.in",
                    phone="9876543213",
                    password_hash=hash_password("Viewer@12345"),
                    role_id=roles[RoleName.VIEWER].id,
                ),
            ]
        )

        session.add(
            CompanySettings(
                company_name="MK Construction & Builders",
                address="No. 42, Bannerghatta Road, Bengaluru, Karnataka 560076",
                mobile="9845012345",
                email="quotes@mkconstruction.in",
                gst_number="29AABCM1234A1Z5",
                quotation_prefix="MKQ",
                default_gst=Decimal("18.00"),
                bank_name="HDFC Bank",
                account_number="50200012345678",
                ifsc_code="HDFC0001234",
            )
        )

        rates = [
            ("Foundation", "CONSTRUCTION", "sqft", "900"),
            ("Ground Floor", "CONSTRUCTION", "sqft", "1800"),
            ("Super Structure", "CONSTRUCTION", "sqft", "1800"),
            ("Terrace", "CONSTRUCTION", "sqft", "1800"),
            ("RCC", "RCC", "sqft", "700"),
            ("Brick & Plaster", "BRICK_PLASTER", "sqft", "350"),
            ("Finishing", "FINISHING", "sqft", "750"),
            ("Black Granite", "GRANITE_TILES", "sqft", "110"),
            ("Kitchen Oota", "GRANITE_TILES", "sqft", "200"),
            ("Floor Tiles", "GRANITE_TILES", "sqft", "60"),
            ("Wall Tiles", "GRANITE_TILES", "sqft", "40"),
            ("Parking Tiles", "GRANITE_TILES", "sqft", "35"),
            ("Sliding Window", "SLIDING", "sqft", "300"),
            ("Main Door Teak", "DOORS_FRAMES", "nos", "28000"),
            ("Internal Flush Door", "DOORS_FRAMES", "nos", "8500"),
        ]
        session.add_all(
            [
                RateMaster(name=n, category=c, unit=u, rate=Decimal(r), is_active=True)
                for n, c, u, r in rates
            ]
        )

        session.add_all(
            [
                MaterialMaster(
                    name="OPC 53 Grade Cement",
                    category="RCC",
                    brand="UltraTech",
                    specification="53 grade OPC",
                    unit="bag",
                    is_active=True,
                ),
                MaterialMaster(
                    name="TMT Bars Fe550",
                    category="RCC",
                    brand="JSW",
                    specification="8mm to 20mm",
                    unit="kg",
                    is_active=True,
                ),
                MaterialMaster(
                    name="Table Moulded Bricks",
                    category="BRICK_PLASTER",
                    brand="Local",
                    specification="Standard size",
                    unit="nos",
                    is_active=True,
                ),
                MaterialMaster(
                    name="Vitrified Floor Tiles 2x2",
                    category="GRANITE_TILES",
                    brand="Kajaria",
                    specification="600x600 mm",
                    unit="sqft",
                    is_active=True,
                ),
                MaterialMaster(
                    name="Finolex Wires 1.5 sqmm",
                    category="ELECTRICAL",
                    brand="Finolex",
                    specification="FRLS copper",
                    unit="m",
                    is_active=True,
                ),
                MaterialMaster(
                    name="Ashirvad CPVC Pipes",
                    category="PLUMBING",
                    brand="Ashirvad",
                    specification="SDR 11",
                    unit="m",
                    is_active=True,
                ),
                MaterialMaster(
                    name="Teak Wood Door Frame",
                    category="DOORS_FRAMES",
                    brand="Local Teak",
                    specification="5 inch frame",
                    unit="cft",
                    is_active=True,
                ),
                MaterialMaster(
                    name="UPVC Sliding Profile",
                    category="SLIDING",
                    brand="Fenesta",
                    specification="2 track",
                    unit="sqft",
                    is_active=True,
                ),
                MaterialMaster(
                    name="Weather Coat Exterior Paint",
                    category="PAINTING",
                    brand="Asian Paints",
                    specification="Apex Ultima",
                    unit="ltr",
                    is_active=True,
                ),
            ]
        )

        electrical = [
            ("Light", "LIGHTING", "nos", "450"),
            ("Fan", "FAN", "nos", "1800"),
            ("Main Board Socket", "SOCKET", "nos", "350"),
            ("TV Socket", "SOCKET", "nos", "400"),
            ("AC Point", "POWER", "nos", "1200"),
            ("Charging Socket", "SOCKET", "nos", "300"),
            ("Bell", "GENERAL", "nos", "250"),
            ("Washing Machine", "POWER", "nos", "800"),
            ("Balcony Light", "LIGHTING", "nos", "500"),
            ("Kitchen Point", "POWER", "nos", "450"),
            ("Oven Point", "POWER", "nos", "900"),
            ("Fridge Point", "POWER", "nos", "700"),
            ("Exhaust Fan", "FAN", "nos", "1500"),
            ("Mirror Light", "LIGHTING", "nos", "650"),
            ("Geyser Point", "POWER", "nos", "900"),
            ("Earthing", "SAFETY", "nos", "4500"),
        ]
        session.add_all(
            [
                ElectricalMaster(name=n, category=c, unit=u, rate=Decimal(r), is_active=True)
                for n, c, u, r in electrical
            ]
        )

        plumbing = [
            ("Underground Water Tank", "TANK", "ltr", "18"),
            ("Terrace Tank", "TANK", "ltr", "12"),
            ("Mixer", "FITTING", "nos", "4500"),
            ("Tap", "FITTING", "nos", "1200"),
            ("Shower", "FITTING", "nos", "2800"),
            ("Basin", "SANITARY", "nos", "5500"),
            ("English Commode", "SANITARY", "nos", "8500"),
            ("Flush", "FITTING", "nos", "2200"),
        ]
        session.add_all(
            [
                PlumbingMaster(name=n, category=c, unit=u, rate=Decimal(r), is_active=True)
                for n, c, u, r in plumbing
            ]
        )

        session.add_all(
            [
                DoorWindowMaster(name="Main Door Teak", category="DOOR", unit="nos", rate=Decimal("28000"), is_active=True),
                DoorWindowMaster(name="Internal Flush Door", category="DOOR", unit="nos", rate=Decimal("8500"), is_active=True),
                DoorWindowMaster(name="Bathroom PVC Door", category="DOOR", unit="nos", rate=Decimal("4500"), is_active=True),
                DoorWindowMaster(name="Teak Door Frame", category="FRAME", unit="nos", rate=Decimal("6500"), is_active=True),
                DoorWindowMaster(name="UPVC Sliding Window", category="WINDOW", unit="sqft", rate=Decimal("300"), is_active=True),
                DoorWindowMaster(name="Ventilator", category="WINDOW", unit="sqft", rate=Decimal("220"), is_active=True),
            ]
        )
        session.add_all(
            [
                TileGraniteMaster(name="Floor Tiles", category="TILE", unit="sqft", rate=Decimal("60"), is_active=True),
                TileGraniteMaster(name="Wall Tiles", category="TILE", unit="sqft", rate=Decimal("40"), is_active=True),
                TileGraniteMaster(name="Parking Tiles", category="TILE", unit="sqft", rate=Decimal("35"), is_active=True),
                TileGraniteMaster(name="Black Granite", category="GRANITE", unit="sqft", rate=Decimal("110"), is_active=True),
                TileGraniteMaster(name="Kitchen Oota Granite", category="GRANITE", unit="sqft", rate=Decimal("200"), is_active=True),
            ]
        )
        session.add_all(
            [
                PaintingMaster(name="Exterior Weather Coat", category="OUTER", unit="sqft", rate=Decimal("28"), is_active=True),
                PaintingMaster(name="Interior Emulsion", category="INNER", unit="sqft", rate=Decimal("22"), is_active=True),
                PaintingMaster(name="Putty + Primer", category="INNER", unit="sqft", rate=Decimal("12"), is_active=True),
            ]
        )
        session.add_all(
            [
                Term(
                    title="Payment Schedule",
                    content="40% on agreement, 30% on plinth, 20% on roof, 10% on handover.",
                    category="PAYMENT",
                    is_default=True,
                    is_active=True,
                ),
                Term(
                    title="GST",
                    content="GST as applicable will be charged extra unless included in the quotation.",
                    category="TAX",
                    is_default=True,
                    is_active=True,
                ),
                Term(
                    title="Scope",
                    content="Quotation covers civil work as listed. Extra items will be billed separately.",
                    category="SCOPE",
                    is_default=True,
                    is_active=True,
                ),
                Term(
                    title="Validity",
                    content="This quotation is valid for 30 days from the quotation date.",
                    category="VALIDITY",
                    is_default=True,
                    is_active=True,
                ),
            ]
        )

        customers = [
            Customer(
                customer_code="MKC-0001",
                name="Ramesh Kumar",
                mobile="9845098765",
                email="ramesh.kumar@example.com",
                customer_type="INDIVIDUAL",
                address="12th Cross, Jayanagar",
                city="Bengaluru",
                state="Karnataka",
                pincode="560041",
                is_active=True,
            ),
            Customer(
                customer_code="MKC-0002",
                name="Lakshmi Developers",
                mobile="9900112233",
                email="accounts@lakshmidev.in",
                customer_type="COMPANY",
                address="Whitefield Main Road",
                city="Bengaluru",
                state="Karnataka",
                pincode="560066",
                is_active=True,
            ),
        ]
        session.add_all(customers)
        await session.flush()
        session.add_all(
            [
                Project(
                    project_code="MKP-0001",
                    customer_id=customers[0].id,
                    project_name="Ramesh G+1 Residence",
                    site_address="Survey No. 18, Kanakapura Road, Bengaluru",
                    plot_area=Decimal("1200"),
                    construction_area=Decimal("2000"),
                    number_of_floors=2,
                    floor_type="G+1",
                    status="PLANNING",
                ),
                Project(
                    project_code="MKP-0002",
                    customer_id=customers[1].id,
                    project_name="Lakshmi Duplex Villa",
                    site_address="Plot 9, Whitefield, Bengaluru",
                    plot_area=Decimal("2400"),
                    construction_area=Decimal("3600"),
                    number_of_floors=2,
                    floor_type="G+1",
                    status="IN_PROGRESS",
                ),
            ]
        )
        await session.commit()
        print("Seed completed.")
        print("Admin login: admin@mkconstruction.in / Admin@12345")


if __name__ == "__main__":
    asyncio.run(seed())
