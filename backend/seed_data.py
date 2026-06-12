"""
AeroVault Seed Data
===================
Populates the database with realistic airport operations data on first run.
Skips seeding if data already exists.

Airport context: Cairo International Airport (CAI / HECA)
- Egypt's busiest airport, hub for EgyptAir (MS)
- International connections to 80+ destinations
- ~14 million passengers/year
- 3 terminals: Terminal 2 (international), Terminal 3 (EgyptAir hub), Terminal 1 (domestic/cargo)
"""

from sqlalchemy.orm import Session
from database import SessionLocal
from models import (
    User, UserRole, NotificationMode,
    Flight, FlightStatus, FlightType,
    CrewMember, CrewAssignment, CrewRole, CrewStatus,
    Aircraft, MaintenanceLog, MELItem, AOGRecord,
    CheckType, MaintStatus, Priority, AOGStatus, LicenseType,
)
from auth.security import hash_password, generate_totp_secret, get_totp_uri, get_current_totp
from datetime import datetime, timezone, timedelta
import qrcode
import io
import os


def seed_database():
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            return  # Already seeded
        print("🌱  Seeding AeroVault database...")
        _seed_users(db)
        _seed_aircraft(db)
        _seed_flights(db)
        _seed_crew(db)
        _seed_crew_assignments(db)
        _seed_maintenance(db)
        print("✅  Seed complete. System ready.")
    finally:
        db.close()


# ─── USERS ────────────────────────────────────────────────────────────────

def _seed_users(db: Session):
    # Superuser gets TOTP
    su_secret = generate_totp_secret()
    su_uri    = get_totp_uri(su_secret, "superuser")
    current_code = get_current_totp(su_secret)

    # Print setup info prominently
    print("\n" + "═"*60)
    print("  SUPERUSER CREDENTIALS")
    print("═"*60)
    print("  Username : superuser")
    print("  Password : AeroVault@2024!")
    print(f"  TOTP URI : {su_uri}")
    print(f"  Current TOTP code: {current_code}  (valid ~30s)")
    print("")
    print("  ➜  Scan the QR code with Google Authenticator")
    print("     (QR saved to: backend/superuser_totp_qr.png)")
    print("═"*60 + "\n")

    # Save QR code image
    try:
        qr = qrcode.QRCode(box_size=8, border=4)
        qr.add_data(su_uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        qr_path = os.path.join(os.path.dirname(__file__), "superuser_totp_qr.png")
        img.save(qr_path)
    except Exception as e:
        print(f"  (QR image not saved: {e})")

    users = [
        # ── Superuser ──
        User(
            username="superuser",
            full_name="System Administrator",
            email="superuser@aerovault.internal",
            department="IT Operations",
            employee_id="SYS-00001",
            hashed_password=hash_password("AeroVault@2024!"),
            totp_secret=su_secret,
            role=UserRole.SUPERUSER,
            notification_mode=NotificationMode.WORK,
            avatar_initials="SU",
        ),
        # ── Admins ──
        User(
            username="ahmed.hassan",
            full_name="Ahmed Hassan",
            email="a.hassan@aerovault.aero",
            department="Airport Operations",
            employee_id="ADM-00101",
            hashed_password=hash_password("Admin#Cairo1"),
            role=UserRole.ADMIN,
            notification_mode=NotificationMode.WORK,
            avatar_initials="AH",
        ),
        User(
            username="sara.ibrahim",
            full_name="Sara Ibrahim",
            email="s.ibrahim@aerovault.aero",
            department="HR & Compliance",
            employee_id="ADM-00102",
            hashed_password=hash_password("Admin#Cairo2"),
            role=UserRole.ADMIN,
            notification_mode=NotificationMode.STANDARD,
            avatar_initials="SI",
        ),
        # ── Flight Managers ──
        User(
            username="omar.nasser",
            full_name="Omar Nasser",
            email="o.nasser@aerovault.aero",
            department="Flight Operations",
            employee_id="FMG-00201",
            hashed_password=hash_password("Flight@Ops1"),
            role=UserRole.FLIGHT_MANAGER,
            notification_mode=NotificationMode.WORK,
            avatar_initials="ON",
        ),
        User(
            username="layla.khalil",
            full_name="Layla Khalil",
            email="l.khalil@aerovault.aero",
            department="Flight Operations",
            employee_id="FMG-00202",
            hashed_password=hash_password("Flight@Ops2"),
            role=UserRole.FLIGHT_MANAGER,
            notification_mode=NotificationMode.WORK,
            avatar_initials="LK",
        ),
        # ── Maintenance Chief ──
        User(
            username="mahmoud.sayed",
            full_name="Mahmoud Sayed",
            email="m.sayed@aerovault.aero",
            department="Line Maintenance",
            employee_id="MNT-00301",
            hashed_password=hash_password("Maint#Chief1"),
            role=UserRole.MAINT_CHIEF,
            notification_mode=NotificationMode.WORK,
            avatar_initials="MS",
        ),
        User(
            username="hana.mostafa",
            full_name="Hana Mostafa",
            email="h.mostafa@aerovault.aero",
            department="Heavy Maintenance",
            employee_id="MNT-00302",
            hashed_password=hash_password("Maint#Chief2"),
            role=UserRole.MAINT_CHIEF,
            notification_mode=NotificationMode.STANDARD,
            avatar_initials="HM",
        ),
        # ── Viewers / Workers ──
        User(
            username="karim.ali",
            full_name="Karim Ali",
            email="k.ali@aerovault.aero",
            department="Ground Handling",
            employee_id="WRK-00401",
            hashed_password=hash_password("Worker@Cairo1"),
            role=UserRole.VIEWER,
            notification_mode=NotificationMode.STANDARD,
            avatar_initials="KA",
        ),
        User(
            username="nour.ramadan",
            full_name="Nour Ramadan",
            email="n.ramadan@aerovault.aero",
            department="Passenger Services",
            employee_id="WRK-00402",
            hashed_password=hash_password("Worker@Cairo2"),
            role=UserRole.VIEWER,
            notification_mode=NotificationMode.MINIMAL,
            avatar_initials="NR",
        ),
        User(
            username="youssef.mansour",
            full_name="Youssef Mansour",
            email="y.mansour@aerovault.aero",
            department="Security",
            employee_id="WRK-00403",
            hashed_password=hash_password("Worker@Cairo3"),
            role=UserRole.VIEWER,
            notification_mode=NotificationMode.MINIMAL,
            avatar_initials="YM",
        ),
    ]
    db.add_all(users)
    db.commit()
    print(f"  ✓ {len(users)} users created")


# ─── AIRCRAFT ─────────────────────────────────────────────────────────────

def _seed_aircraft(db: Session):
    now = datetime.now(timezone.utc)
    aircraft_list = [
        # ── EgyptAir Fleet ──
        Aircraft(
            registration="SU-GEA", airline_iata="MS", airline_name="EgyptAir",
            aircraft_type="Boeing 737-800", icao_type="B738", manufacturer="Boeing",
            msn="39274", year_of_manufacture=2013, delivery_date="2013-05-14",
            engine_type="CFM56-7B27", engine_count=2,
            total_flight_hours=24817.5, total_cycles=18934, max_cycles=75000,
            hours_since_last_a=312.0, hours_since_last_c=1840.0,
            next_a_check_due="2024-11-15", next_c_check_due="2026-03-01",
            is_active=True, is_aog=False, current_airport="CAI", home_base="CAI",
            airworthiness_cert="ECAR-AW-2024-00341", cert_expiry="2025-05-14",
            noise_cert="ICAO Chapter 4",
        ),
        Aircraft(
            registration="SU-GEB", airline_iata="MS", airline_name="EgyptAir",
            aircraft_type="Boeing 737-800", icao_type="B738", manufacturer="Boeing",
            msn="39275", year_of_manufacture=2013, delivery_date="2013-07-22",
            engine_type="CFM56-7B27", engine_count=2,
            total_flight_hours=23102.0, total_cycles=17508, max_cycles=75000,
            hours_since_last_a=487.0, hours_since_last_c=2210.0,
            next_a_check_due="2024-10-28", next_c_check_due="2026-07-15",
            is_active=True, is_aog=False, current_airport="LHR", home_base="CAI",
            airworthiness_cert="ECAR-AW-2024-00342", cert_expiry="2025-07-22",
            noise_cert="ICAO Chapter 4",
        ),
        Aircraft(
            registration="SU-GEC", airline_iata="MS", airline_name="EgyptAir",
            aircraft_type="Airbus A320-214", icao_type="A320", manufacturer="Airbus",
            msn="5812", year_of_manufacture=2014, delivery_date="2014-03-10",
            engine_type="CFM56-5B4/P", engine_count=2,
            total_flight_hours=19650.0, total_cycles=15420, max_cycles=60000,
            hours_since_last_a=205.5, hours_since_last_c=980.0,
            next_a_check_due="2025-01-10", next_c_check_due="2027-02-28",
            is_active=True, is_aog=False, current_airport="CAI", home_base="CAI",
            airworthiness_cert="ECAR-AW-2024-00397", cert_expiry="2025-03-10",
            noise_cert="ICAO Chapter 4",
        ),
        Aircraft(
            registration="SU-GED", airline_iata="MS", airline_name="EgyptAir",
            aircraft_type="Airbus A320-214", icao_type="A320", manufacturer="Airbus",
            msn="5891", year_of_manufacture=2014, delivery_date="2014-09-05",
            engine_type="CFM56-5B4/P", engine_count=2,
            total_flight_hours=18900.0, total_cycles=14810,
            hours_since_last_a=156.0, hours_since_last_c=750.0,
            next_a_check_due="2025-02-20", next_c_check_due="2027-06-30",
            is_active=True, is_aog=True,   # Currently AOG!
            current_airport="CAI", home_base="CAI",
            airworthiness_cert="ECAR-AW-2024-00401", cert_expiry="2025-09-05",
            notes="AOG: hydraulic system fault — see AOG-2024-0089",
        ),
        Aircraft(
            registration="SU-GEE", airline_iata="MS", airline_name="EgyptAir",
            aircraft_type="Boeing 777-300ER", icao_type="B77W", manufacturer="Boeing",
            msn="41341", year_of_manufacture=2010, delivery_date="2010-11-20",
            engine_type="GE90-115BL", engine_count=2,
            total_flight_hours=51240.0, total_cycles=12844, max_cycles=40000,
            hours_since_last_a=418.0, hours_since_last_c=3200.0,
            next_a_check_due="2024-12-01", next_c_check_due="2025-11-15",
            is_active=True, is_aog=False, current_airport="CAI", home_base="CAI",
            airworthiness_cert="ECAR-AW-2024-00210", cert_expiry="2024-11-20",
            noise_cert="ICAO Chapter 4",
        ),
        Aircraft(
            registration="SU-GEF", airline_iata="MS", airline_name="EgyptAir",
            aircraft_type="Boeing 777-300ER", icao_type="B77W", manufacturer="Boeing",
            msn="41342", year_of_manufacture=2011, delivery_date="2011-04-08",
            engine_type="GE90-115BL", engine_count=2,
            total_flight_hours=48710.0, total_cycles=12100,
            hours_since_last_a=289.5, hours_since_last_c=2890.0,
            next_a_check_due="2025-03-15", next_c_check_due="2026-04-08",
            is_active=True, is_aog=False, current_airport="JFK", home_base="CAI",
            airworthiness_cert="ECAR-AW-2024-00218", cert_expiry="2025-04-08",
        ),
        Aircraft(
            registration="SU-GEG", airline_iata="MS", airline_name="EgyptAir",
            aircraft_type="Airbus A330-343", icao_type="A333", manufacturer="Airbus",
            msn="1287", year_of_manufacture=2012, delivery_date="2012-06-18",
            engine_type="Trent 772B-60", engine_count=2,
            total_flight_hours=38420.0, total_cycles=9810,
            hours_since_last_a=92.0, hours_since_last_c=1100.0,
            next_a_check_due="2025-05-20", next_c_check_due="2028-01-18",
            is_active=True, is_aog=False, current_airport="CAI", home_base="CAI",
            airworthiness_cert="ECAR-AW-2024-00302", cert_expiry="2025-06-18",
        ),

    ]
    db.add_all(aircraft_list)
    db.commit()
    print(f"  ✓ {len(aircraft_list)} aircraft in fleet registry")


# ─── FLIGHTS ──────────────────────────────────────────────────────────────

def _seed_flights(db: Session):
    now = datetime.now(timezone.utc)

    def hm(h, m=0):
        """Return a UTC datetime offset from now by +h hours +m minutes."""
        return now + timedelta(hours=h, minutes=m)

    flights = [
        # ── Departures from CAI ──
        Flight(
            flight_number="MS986", airline_iata="MS", airline_name="EgyptAir",
            callsign="MSR986",
            origin_iata="CAI", origin_city="Cairo", origin_country="Egypt",
            dest_iata="LHR",   dest_city="London",  dest_country="United Kingdom",
            aircraft_reg="SU-GEE", aircraft_type="Boeing 777-300ER", aircraft_icao="B77W",
            flight_type=FlightType.INTERNATIONAL,
            scheduled_dep=hm(-0.5), scheduled_arr=hm(5.5),
            estimated_dep=hm(-0.5), delay_minutes=0,
            status=FlightStatus.DEPARTED,
            terminal="T3", gate="G14", check_in_desk="D21-D26",
            total_seats=396, passengers_booked=381, cargo_kg=4200.0, fuel_kg=71400.0,
            altitude_ft=34000, speed_kts=478, latitude=34.2, longitude=18.4,
        ),
        Flight(
            flight_number="MS777", airline_iata="MS", airline_name="EgyptAir",
            callsign="MSR777",
            origin_iata="CAI", origin_city="Cairo", origin_country="Egypt",
            dest_iata="JFK",   dest_city="New York", dest_country="United States",
            aircraft_reg="SU-GEF", aircraft_type="Boeing 777-300ER", aircraft_icao="B77W",
            flight_type=FlightType.INTERNATIONAL,
            scheduled_dep=hm(-3), scheduled_arr=hm(9),
            actual_dep=hm(-3.1),
            status=FlightStatus.EN_ROUTE,
            terminal="T3", gate="G18", check_in_desk="D27-D32",
            total_seats=396, passengers_booked=394, cargo_kg=5100.0, fuel_kg=89000.0,
            altitude_ft=37000, speed_kts=502, latitude=41.8, longitude=-12.3,
            remarks="Live position data from OpenSky Network when available.",
        ),
        Flight(
            flight_number="MS200", airline_iata="MS", airline_name="EgyptAir",
            callsign="MSR200",
            origin_iata="CAI", origin_city="Cairo", origin_country="Egypt",
            dest_iata="DXB",   dest_city="Dubai",   dest_country="United Arab Emirates",
            aircraft_reg="SU-GEA", aircraft_type="Boeing 737-800", aircraft_icao="B738",
            flight_type=FlightType.INTERNATIONAL,
            scheduled_dep=hm(1), scheduled_arr=hm(4),
            estimated_dep=hm(1), delay_minutes=0,
            status=FlightStatus.BOARDING,
            terminal="T3", gate="G22", check_in_desk="D33-D36", baggage_belt="Belt 4",
            total_seats=162, passengers_booked=155, cargo_kg=1800.0, fuel_kg=12500.0,
        ),
        Flight(
            flight_number="MS760", airline_iata="MS", airline_name="EgyptAir",
            callsign="MSR760",
            origin_iata="CAI", origin_city="Cairo", origin_country="Egypt",
            dest_iata="CDG",   dest_city="Paris",   dest_country="France",
            aircraft_reg="SU-GEG", aircraft_type="Airbus A330-343", aircraft_icao="A333",
            flight_type=FlightType.INTERNATIONAL,
            scheduled_dep=hm(2.5), scheduled_arr=hm(8),
            estimated_dep=hm(3, 25), delay_minutes=55, delay_reason="Late inbound aircraft",
            status=FlightStatus.DELAYED,
            terminal="T3", gate="G08", check_in_desk="D10-D16",
            total_seats=284, passengers_booked=271, cargo_kg=3400.0, fuel_kg=42000.0,
        ),
        Flight(
            flight_number="MS804", airline_iata="MS", airline_name="EgyptAir",
            callsign="MSR804",
            origin_iata="CAI", origin_city="Cairo", origin_country="Egypt",
            dest_iata="DME",   dest_city="Moscow", dest_country="Russia",
            aircraft_reg="SU-GEB", aircraft_type="Boeing 737-800", aircraft_icao="B738",
            flight_type=FlightType.INTERNATIONAL,
            scheduled_dep=hm(4), scheduled_arr=hm(8),
            estimated_dep=hm(4), delay_minutes=0,
            status=FlightStatus.SCHEDULED,
            terminal="T3", gate="G11", check_in_desk="D17-D20",
            total_seats=162, passengers_booked=98,
        ),
        Flight(
            flight_number="MS317", airline_iata="MS", airline_name="EgyptAir",
            callsign="MSR317",
            origin_iata="CAI", origin_city="Cairo", origin_country="Egypt",
            dest_iata="SSH",   dest_city="Sharm El-Sheikh", dest_country="Egypt",
            aircraft_reg="SU-GEC", aircraft_type="Airbus A320-214", aircraft_icao="A320",
            flight_type=FlightType.DOMESTIC,
            scheduled_dep=hm(0.75), scheduled_arr=hm(1.75),
            estimated_dep=hm(0.75), delay_minutes=0,
            status=FlightStatus.SCHEDULED,
            terminal="T2", gate="B04", check_in_desk="C01-C04",
            total_seats=150, passengers_booked=144,
        ),
        Flight(
            flight_number="MS399", airline_iata="MS", airline_name="EgyptAir",
            callsign="MSR399",
            origin_iata="CAI", origin_city="Cairo", origin_country="Egypt",
            dest_iata="HRG",   dest_city="Hurghada", dest_country="Egypt",
            aircraft_reg="SU-GED", aircraft_type="Airbus A320-214", aircraft_icao="A320",
            flight_type=FlightType.DOMESTIC,
            scheduled_dep=hm(1.5), scheduled_arr=hm(2.5),
            status=FlightStatus.CANCELLED,
            delay_reason="Aircraft AOG — hydraulic system fault",
            terminal="T2", gate="B07",
            total_seats=150, passengers_booked=139,
            remarks="Passengers rebooked on MS401 (dep +3h). AOG recovery in progress.",
        ),
        # ── EgyptAir Arrivals into CAI ──
        Flight(
            flight_number="MS704", airline_iata="MS", airline_name="EgyptAir",
            callsign="MSR704",
            origin_iata="CDG", origin_city="Paris", origin_country="France",
            dest_iata="CAI",   dest_city="Cairo",   dest_country="Egypt",
            aircraft_reg="SU-GEG", aircraft_type="Airbus A330-343", aircraft_icao="A333",
            flight_type=FlightType.INTERNATIONAL,
            scheduled_dep=hm(-5), scheduled_arr=hm(-0.3),
            estimated_arr=hm(0, 20), delay_minutes=50, delay_reason="ATC slot restriction Paris",
            actual_dep=hm(-4.5),
            status=FlightStatus.APPROACHING,
            terminal="T3", gate="G08",
            altitude_ft=8200, speed_kts=275, latitude=30.4, longitude=31.8,
            total_seats=284, passengers_booked=261,
        ),
        Flight(
            flight_number="MS928", airline_iata="MS", airline_name="EgyptAir",
            callsign="MSR928",
            origin_iata="DXB", origin_city="Dubai", origin_country="United Arab Emirates",
            dest_iata="CAI",   dest_city="Cairo",   dest_country="Egypt",
            aircraft_reg="SU-GEA", aircraft_type="Boeing 737-800", aircraft_icao="B738",
            flight_type=FlightType.INTERNATIONAL,
            scheduled_dep=hm(-4), scheduled_arr=hm(-1),
            actual_dep=hm(-4), actual_arr=hm(-1),
            status=FlightStatus.ON_GROUND,
            terminal="T3", gate="G22", baggage_belt="Belt 4",
            total_seats=162, passengers_booked=155,
        ),
        Flight(
            flight_number="MS986", airline_iata="MS", airline_name="EgyptAir",
            callsign="MSR986",
            origin_iata="LHR", origin_city="London", origin_country="United Kingdom",
            dest_iata="CAI",   dest_city="Cairo",    dest_country="Egypt",
            aircraft_reg="SU-GEE", aircraft_type="Boeing 777-300ER", aircraft_icao="B77W",
            flight_type=FlightType.INTERNATIONAL,
            scheduled_dep=hm(-6), scheduled_arr=hm(-0.5),
            actual_dep=hm(-6), actual_arr=hm(-0.5),
            status=FlightStatus.LANDED,
            terminal="T3", gate="G14", baggage_belt="Belt 7",
            total_seats=396, passengers_booked=381,
        ),
        Flight(
            flight_number="MS108", airline_iata="MS", airline_name="EgyptAir",
            callsign="MSR108",
            origin_iata="LHR", origin_city="London", origin_country="United Kingdom",
            dest_iata="CAI",   dest_city="Cairo",    dest_country="Egypt",
            aircraft_reg="SU-GEE", aircraft_type="Boeing 777-300ER", aircraft_icao="B77W",
            flight_type=FlightType.INTERNATIONAL,
            scheduled_dep=hm(5), scheduled_arr=hm(11.5),
            status=FlightStatus.SCHEDULED,
            terminal="T3", gate="G16",
            total_seats=396, passengers_booked=340,
        ),
        Flight(
            flight_number="MS690", airline_iata="MS", airline_name="EgyptAir",
            callsign="MSR690",
            origin_iata="RUH", origin_city="Riyadh", origin_country="Saudi Arabia",
            dest_iata="CAI",   dest_city="Cairo",    dest_country="Egypt",
            aircraft_reg="SU-GEB", aircraft_type="Boeing 737-800", aircraft_icao="B738",
            flight_type=FlightType.INTERNATIONAL,
            scheduled_dep=hm(3), scheduled_arr=hm(6),
            estimated_dep=hm(3), delay_minutes=0,
            status=FlightStatus.SCHEDULED,
            terminal="T3", gate="G20",
            total_seats=162, passengers_booked=148,
        ),
    ]
    db.add_all(flights)
    db.commit()
    print(f"  ✓ {len(flights)} flights loaded")


# ─── CREW ─────────────────────────────────────────────────────────────────

def _seed_crew(db: Session):
    crew = [
        # ── Captains ──
        CrewMember(
            employee_id="P-00142", full_name="Capt. Tarek El-Gamal",
            nationality="Egyptian", date_of_birth="1970-03-15", gender="Male",
            role=CrewRole.CAPTAIN, status=CrewStatus.ON_DUTY, base_airport="CAI",
            current_airport="CAI", flight_hours_total=18420.5, flight_hours_month=72.0,
            flight_hours_year=810.0, max_hours_month=100.0, max_hours_year=1000.0,
            duty_hours_today=6.5, max_duty_hours=14.0,
            license_type=LicenseType.ATPL, license_number="ECAR-ATPL-00142",
            license_expiry="2026-03-15", medical_class="Class 1",
            medical_expiry="2025-03-15",
            type_ratings=["B77W", "B738", "A320"],
            languages=["Arabic", "English"],
        ),
        CrewMember(
            employee_id="P-00143", full_name="Capt. Ahmed Fawzy",
            nationality="Egyptian", date_of_birth="1972-08-22", gender="Male",
            role=CrewRole.CAPTAIN, status=CrewStatus.AVAILABLE, base_airport="CAI",
            current_airport="CAI", flight_hours_total=16890.0, flight_hours_month=64.5,
            flight_hours_year=720.0,
            license_type=LicenseType.ATPL, license_number="ECAR-ATPL-00143",
            license_expiry="2025-08-22", medical_class="Class 1",
            medical_expiry="2025-02-22",
            type_ratings=["B77W", "B738"],
            languages=["Arabic", "English", "French"],
        ),
        CrewMember(
            employee_id="P-00144", full_name="Capt. Mona El-Sherif",
            nationality="Egyptian", date_of_birth="1975-11-10", gender="Female",
            role=CrewRole.CAPTAIN, status=CrewStatus.RESTING, base_airport="CAI",
            current_airport="CAI", flight_hours_total=14200.0, flight_hours_month=88.0,
            flight_hours_year=940.0, duty_hours_today=0.0,
            license_type=LicenseType.ATPL, license_number="ECAR-ATPL-00144",
            license_expiry="2025-11-10", medical_class="Class 1",
            medical_expiry="2025-05-10",
            type_ratings=["A333", "A320"],
            languages=["Arabic", "English"],
        ),
        # ── First Officers ──
        CrewMember(
            employee_id="P-00201", full_name="FO Omar Rashid",
            nationality="Egyptian", date_of_birth="1985-04-18", gender="Male",
            role=CrewRole.FIRST_OFFICER, status=CrewStatus.ON_DUTY, base_airport="CAI",
            current_airport="CAI", flight_hours_total=6840.0, flight_hours_month=55.0,
            flight_hours_year=610.0,
            license_type=LicenseType.ATPL, license_number="ECAR-ATPL-00201",
            license_expiry="2026-04-18", medical_class="Class 1",
            medical_expiry="2025-04-18",
            type_ratings=["B77W", "B738"],
            languages=["Arabic", "English"],
        ),
        CrewMember(
            employee_id="P-00202", full_name="FO Salma Abdel-Aziz",
            nationality="Egyptian", date_of_birth="1988-07-25", gender="Female",
            role=CrewRole.FIRST_OFFICER, status=CrewStatus.STANDBY, base_airport="CAI",
            current_airport="CAI", flight_hours_total=4210.0, flight_hours_month=42.0,
            flight_hours_year=480.0,
            license_type=LicenseType.ATPL, license_number="ECAR-ATPL-00202",
            license_expiry="2025-07-25", medical_class="Class 1",
            medical_expiry="2025-01-25",
            type_ratings=["A320", "A333"],
            languages=["Arabic", "English", "German"],
        ),
        CrewMember(
            employee_id="P-00203", full_name="FO Khaled Samir",
            nationality="Egyptian", date_of_birth="1990-01-30", gender="Male",
            role=CrewRole.FIRST_OFFICER, status=CrewStatus.AVAILABLE, base_airport="CAI",
            current_airport="CAI", flight_hours_total=3180.0, flight_hours_month=38.0,
            flight_hours_year=420.0,
            license_type=LicenseType.CPL, license_number="ECAR-CPL-00203",
            license_expiry="2025-01-30", medical_class="Class 1",
            medical_expiry="2024-07-30",
            type_ratings=["B738"],
            languages=["Arabic", "English"],
        ),
        # ── Second Officers (Long-haul relief) ──
        CrewMember(
            employee_id="P-00251", full_name="SO Rania Hassan",
            nationality="Egyptian", date_of_birth="1992-09-12", gender="Female",
            role=CrewRole.SECOND_OFFICER, status=CrewStatus.ON_DUTY, base_airport="CAI",
            current_airport="JFK", flight_hours_total=1820.0, flight_hours_month=48.0,
            flight_hours_year=390.0,
            license_type=LicenseType.CPL, license_number="ECAR-CPL-00251",
            license_expiry="2025-09-12", medical_class="Class 1",
            medical_expiry="2025-03-12",
            type_ratings=["B77W"],
            languages=["Arabic", "English"],
        ),
        # ── Pursers & Senior Cabin Crew ──
        CrewMember(
            employee_id="CC-00301", full_name="Purser Heba Kamel",
            nationality="Egyptian", date_of_birth="1982-06-05", gender="Female",
            role=CrewRole.PURSER, status=CrewStatus.ON_DUTY, base_airport="CAI",
            current_airport="CAI", flight_hours_total=12400.0,
            flight_hours_month=78.0, flight_hours_year=850.0,
            license_type=LicenseType.CABIN, license_number="ECAR-CC-00301",
            license_expiry="2025-06-05",
            type_ratings=["B77W", "B738", "A320", "A333"],
            languages=["Arabic", "English", "French", "Italian"],
        ),
        CrewMember(
            employee_id="CC-00302", full_name="Purser Amr Shehab",
            nationality="Egyptian", date_of_birth="1984-12-18", gender="Male",
            role=CrewRole.PURSER, status=CrewStatus.AVAILABLE, base_airport="CAI",
            current_airport="CAI", flight_hours_total=10800.0,
            flight_hours_month=65.0, flight_hours_year=740.0,
            license_type=LicenseType.CABIN, license_number="ECAR-CC-00302",
            license_expiry="2025-12-18",
            type_ratings=["B77W", "A333"],
            languages=["Arabic", "English", "Spanish"],
        ),
        # ── Cabin Crew ──
        CrewMember(
            employee_id="CC-00401", full_name="Yasmine Fouad",
            nationality="Egyptian", date_of_birth="1995-02-28", gender="Female",
            role=CrewRole.CABIN_CREW, status=CrewStatus.ON_DUTY, base_airport="CAI",
            current_airport="LHR", flight_hours_total=2840.0,
            flight_hours_month=60.0, flight_hours_year=680.0,
            license_type=LicenseType.CABIN, license_number="ECAR-CC-00401",
            license_expiry="2025-02-28",
            type_ratings=["B77W", "B738"],
            languages=["Arabic", "English"],
        ),
        CrewMember(
            employee_id="CC-00402", full_name="Mohamed Tawfik",
            nationality="Egyptian", date_of_birth="1996-07-14", gender="Male",
            role=CrewRole.CABIN_CREW, status=CrewStatus.AVAILABLE, base_airport="CAI",
            current_airport="CAI", flight_hours_total=1620.0,
            flight_hours_month=55.0, flight_hours_year=590.0,
            license_type=LicenseType.CABIN, license_number="ECAR-CC-00402",
            license_expiry="2025-07-14",
            type_ratings=["B738", "A320"],
            languages=["Arabic", "English", "Greek"],
        ),
        CrewMember(
            employee_id="CC-00403", full_name="Dina Mahmoud",
            nationality="Egyptian", date_of_birth="1997-11-03", gender="Female",
            role=CrewRole.CABIN_CREW, status=CrewStatus.SICK, base_airport="CAI",
            current_airport="CAI", flight_hours_total=980.0,
            flight_hours_month=12.0, flight_hours_year=340.0,
            license_type=LicenseType.CABIN, license_number="ECAR-CC-00403",
            license_expiry="2025-11-03",
            type_ratings=["A320"],
            languages=["Arabic", "English"],
            notes="On sick leave since 2024-10-15. Expected return 2024-10-28.",
        ),
        CrewMember(
            employee_id="CC-00404", full_name="Sherif Magdy",
            nationality="Egyptian", date_of_birth="1994-04-22", gender="Male",
            role=CrewRole.CABIN_CREW, status=CrewStatus.ON_DUTY, base_airport="CAI",
            current_airport="JFK", flight_hours_total=3210.0,
            flight_hours_month=71.0, flight_hours_year=780.0,
            license_type=LicenseType.CABIN, license_number="ECAR-CC-00404",
            license_expiry="2025-04-22",
            type_ratings=["B77W", "B738", "A333"],
            languages=["Arabic", "English", "Chinese"],
        ),
        # ── Flight Dispatchers ──
        CrewMember(
            employee_id="GD-00501", full_name="Disp. Mazen El-Kady",
            nationality="Egyptian", date_of_birth="1980-09-08", gender="Male",
            role=CrewRole.DISPATCHER, status=CrewStatus.ON_DUTY, base_airport="CAI",
            current_airport="CAI", flight_hours_total=0.0,
            license_type=LicenseType.GROUND, license_number="ECAR-FD-00501",
            license_expiry="2025-09-08",
            type_ratings=["B77W", "B738", "A320", "A333"],
            languages=["Arabic", "English"],
        ),
        # ── Ground Agents ──
        CrewMember(
            employee_id="GD-00601", full_name="Bassem Nabil",
            nationality="Egyptian", date_of_birth="1990-05-17", gender="Male",
            role=CrewRole.GROUND_AGENT, status=CrewStatus.ON_DUTY, base_airport="CAI",
            current_airport="CAI", flight_hours_total=0.0,
            license_type=LicenseType.GROUND, license_number="ECAR-GA-00601",
            license_expiry="2025-05-17",
            languages=["Arabic", "English"],
        ),
        CrewMember(
            employee_id="GD-00602", full_name="Rana Ibrahim",
            nationality="Egyptian", date_of_birth="1993-08-30", gender="Female",
            role=CrewRole.GROUND_AGENT, status=CrewStatus.AVAILABLE, base_airport="CAI",
            current_airport="CAI", flight_hours_total=0.0,
            license_type=LicenseType.GROUND, license_number="ECAR-GA-00602",
            license_expiry="2025-08-30",
            languages=["Arabic", "English", "French"],
        ),
    ]
    db.add_all(crew)
    db.commit()
    print(f"  ✓ {len(crew)} crew members loaded")


# ─── CREW ASSIGNMENTS ─────────────────────────────────────────────────────

def _seed_crew_assignments(db: Session):
    db_flights = {f.flight_number: f for f in db.query(Flight).all()}
    db_crew    = {c.employee_id:   c for c in db.query(CrewMember).all()}

    assignments = [
        # MS986 CAI→LHR (departed, Boeing 777-300ER)
        CrewAssignment(flight_id=db_flights["MS986"].id, crew_member_id=db_crew["P-00142"].id,
                       role_on_flight=CrewRole.CAPTAIN,       assigned_by="omar.nasser"),
        CrewAssignment(flight_id=db_flights["MS986"].id, crew_member_id=db_crew["P-00201"].id,
                       role_on_flight=CrewRole.FIRST_OFFICER,  assigned_by="omar.nasser"),
        CrewAssignment(flight_id=db_flights["MS986"].id, crew_member_id=db_crew["CC-00301"].id,
                       role_on_flight=CrewRole.PURSER,         assigned_by="omar.nasser"),
        CrewAssignment(flight_id=db_flights["MS986"].id, crew_member_id=db_crew["CC-00401"].id,
                       role_on_flight=CrewRole.CABIN_CREW,     assigned_by="omar.nasser"),
        # MS777 CAI→JFK (en route, Boeing 777-300ER)
        CrewAssignment(flight_id=db_flights["MS777"].id, crew_member_id=db_crew["P-00143"].id,
                       role_on_flight=CrewRole.CAPTAIN,        assigned_by="layla.khalil"),
        CrewAssignment(flight_id=db_flights["MS777"].id, crew_member_id=db_crew["P-00251"].id,
                       role_on_flight=CrewRole.SECOND_OFFICER, assigned_by="layla.khalil"),
        CrewAssignment(flight_id=db_flights["MS777"].id, crew_member_id=db_crew["CC-00404"].id,
                       role_on_flight=CrewRole.CABIN_CREW,     assigned_by="layla.khalil"),
        # MS200 CAI→DXB (boarding)
        CrewAssignment(flight_id=db_flights["MS200"].id, crew_member_id=db_crew["P-00142"].id,
                       role_on_flight=CrewRole.CAPTAIN,        assigned_by="omar.nasser"),
        CrewAssignment(flight_id=db_flights["MS200"].id, crew_member_id=db_crew["P-00203"].id,
                       role_on_flight=CrewRole.FIRST_OFFICER,  assigned_by="omar.nasser"),
        CrewAssignment(flight_id=db_flights["MS200"].id, crew_member_id=db_crew["CC-00402"].id,
                       role_on_flight=CrewRole.CABIN_CREW,     assigned_by="omar.nasser"),
    ]
    db.add_all(assignments)
    db.commit()
    print(f"  ✓ {len(assignments)} crew assignments made")


# ─── MAINTENANCE ──────────────────────────────────────────────────────────

def _seed_maintenance(db: Session):
    now = datetime.now(timezone.utc)
    db_aircraft = {a.registration: a for a in db.query(Aircraft).all()}

    def hm(h):
        return now + timedelta(hours=h)

    # ── Maintenance Logs ──
    maint_logs = [
        # SU-GEA — Scheduled A-Check
        MaintenanceLog(
            aircraft_id=db_aircraft["SU-GEA"].id,
            task_number="MNT-2024-00821",
            check_type=CheckType.A_CHECK,
            status=MaintStatus.SCHEDULED,
            priority=Priority.ROUTINE,
            title="A-Check — 500 FH Inspection",
            description="Standard 500 flight-hour A-check covering all routine inspections per MPD (Maintenance Planning Document). Includes lubrication, fluid checks, visual inspections of all systems, engine run-up.",
            ata_chapter="ATA 05", ata_description="Periodic Inspections",
            scheduled_start=hm(48), scheduled_end=hm(60),
            lead_technician="Ibrahim Al-Rashidy", technicians=["Hossam Farag", "Magdy Saad"],
            hangar_bay="Hangar 1, Bay A",
            man_hours_est=48.0, parts_required=[
                {"part_number": "MS28775-010", "description": "O-Ring Kit", "qty": 4, "status": "in_stock"},
                {"part_number": "CM-6004", "description": "Engine Oil (Mobil Jet Oil II)", "qty": 12, "status": "in_stock"},
            ],
            parts_cost_usd=840.0, labor_cost_usd=6200.0,
            work_order_ref="WO-2024-00821",
            next_due_hours=500.0, next_due_date="2025-04-15",
        ),
        # SU-GEE — Engine Borescope
        MaintenanceLog(
            aircraft_id=db_aircraft["SU-GEE"].id,
            task_number="MNT-2024-00798",
            check_type=CheckType.ENGINE_BORESCOPE,
            status=MaintStatus.IN_PROGRESS,
            priority=Priority.URGENT,
            title="GE90 Engine #2 Borescope Inspection",
            description="Borescope inspection of GE90-115BL Engine #2 following crew report of increased EGT margin loss. Inspecting HPT blades, combustion liner, and LPT stage 1-4. EGT trend monitoring triggered this inspection after 85°C margin loss over 200 cycles.",
            ata_chapter="ATA 72", ata_description="Engine",
            scheduled_start=hm(-4), scheduled_end=hm(4),
            actual_start=hm(-4),
            lead_technician="Walid Abdel-Hamid (GE Certified AME)", technicians=["Tarek Samir", "Adel Fouad"],
            hangar_bay="Engine Bay 2",
            man_hours_est=16.0, man_hours_actual=8.5,
            parts_required=[
                {"part_number": "GE90-1042A1", "description": "HPT Stage 1 Blade (TBD)", "qty": 0, "status": "pending_inspection"},
            ],
            work_order_ref="WO-2024-00798",
            ad_number="FAA AD 2023-14-08",
            findings="Mild HPT stage 1 blade tip oxidation observed. No cracks. Monitoring continued.",
        ),
        # SU-GED — AOG (hydraulic fault)
        MaintenanceLog(
            aircraft_id=db_aircraft["SU-GED"].id,
            task_number="MNT-2024-00841",
            check_type=CheckType.UNSCHEDULED,
            status=MaintStatus.IN_PROGRESS,
            priority=Priority.AOG,
            title="Hydraulic System Fault — Green System Low Pressure",
            description="ECAM HYDRAULIC GREEN SYS LO PR triggered on approach. Captain elected to declare PAN-PAN and divert to Cairo. Green hydraulic system pressure dropped to 1200 PSI (normal: 3000 PSI). Inspection revealed crack in Green system pump pressure line fitting (ATA 29). Aircraft grounded. Parts on order from Airbus AOG Centre Hamburg.",
            ata_chapter="ATA 29", ata_description="Hydraulic Power",
            scheduled_start=hm(-2), scheduled_end=hm(36),
            actual_start=hm(-2),
            lead_technician="Mahmoud Sayed (Licensed AME — ECAR)", technicians=["Ayman Gaber", "Fady Naguib", "Hatem Ramzy"],
            hangar_bay="Hangar 2, Bay C",
            man_hours_est=28.0, man_hours_actual=4.0,
            parts_required=[
                {"part_number": "C20720-5100", "description": "Hydraulic Pump Pressure Line Fitting (Green)", "qty": 2, "status": "on_order_aog"},
                {"part_number": "C20720-5101", "description": "Hydraulic Fluid (Skydrol LD4)", "qty": 6, "status": "in_stock"},
            ],
            parts_cost_usd=18400.0, labor_cost_usd=3800.0,
            work_order_ref="WO-2024-00841",
            findings="Fatigue crack in Green hydraulic pressure line fitting P/N C20720-5100. Fitting replaced. System flush and functional test pending.",
        ),
        # SU-GEB — Cabin Inspection
        MaintenanceLog(
            aircraft_id=db_aircraft["SU-GEB"].id,
            task_number="MNT-2024-00752",
            check_type=CheckType.CABIN,
            status=MaintStatus.COMPLETED,
            priority=Priority.ROUTINE,
            title="Cabin Interior Inspection & Seat Repair",
            description="Periodic cabin inspection per airline maintenance program. 12F business class and 138Y economy seats inspected. Seat recline mechanism on 14C (economy) found unserviceable. Seat 21A tray table cracked. Overhead bin latch row 28 requires adjustment.",
            ata_chapter="ATA 25", ata_description="Equipment/Furnishings",
            scheduled_start=hm(-72), scheduled_end=hm(-64),
            actual_start=hm(-72), actual_end=hm(-65),
            lead_technician="Essam Khalil", technicians=["Mahmoud Ibrahim"],
            hangar_bay="Hangar 1, Line Maintenance",
            man_hours_est=8.0, man_hours_actual=7.0,
            parts_required=[
                {"part_number": "ECA-35-4401", "description": "Seat Recline Actuator Assembly", "qty": 1, "status": "installed"},
                {"part_number": "ECA-25-TT01", "description": "Economy Tray Table Replacement", "qty": 1, "status": "installed"},
            ],
            parts_cost_usd=2100.0, labor_cost_usd=1400.0,
            work_order_ref="WO-2024-00752",
            corrective_action="Seat 14C recline actuator replaced. Tray table 21A replaced. Bin latch 28 adjusted and tested serviceable.",
            approved_by="Mahmoud Sayed", license_number="ECAR-AME-00301",
            sign_off_time=hm(-65),
        ),
        # SU-GEG — C-Check upcoming
        MaintenanceLog(
            aircraft_id=db_aircraft["SU-GEG"].id,
            task_number="MNT-2024-00799",
            check_type=CheckType.C_CHECK,
            status=MaintStatus.SCHEDULED,
            priority=Priority.ROUTINE,
            title="C3-Check — 18-Month Heavy Maintenance Visit",
            description="Full C3-Check per Airbus A330 MPD. Major structural inspections, all access panels opened, full wiring harness inspection, hydraulic system overhaul, landing gear detailed inspection, fuel tank entry and inspection, all doors and emergency equipment overhaul.",
            ata_chapter="ATA 05", ata_description="Periodic Inspections",
            scheduled_start=hm(24*30), scheduled_end=hm(24*44),  # ~30 days from now, 14-day check
            lead_technician="TBD — MRO Facility", technicians=[],
            hangar_bay="MRO Facility — Egyptair Technical (EGTS), Cairo",
            man_hours_est=10000.0, labor_cost_usd=2800000.0, parts_cost_usd=1200000.0,
            work_order_ref="WO-2024-00799-C3",
            next_due_date="2026-09-18",
        ),
        # SU-GEA — AD Compliance
        MaintenanceLog(
            aircraft_id=db_aircraft["SU-GEA"].id,
            task_number="MNT-2024-00815",
            check_type=CheckType.AD_COMPLIANCE,
            status=MaintStatus.COMPLETED,
            priority=Priority.URGENT,
            title="FAA AD 2024-09-12 — Boeing 737 Fuselage Frame Inspection",
            description="Mandatory compliance with FAA Airworthiness Directive 2024-09-12 requiring one-time detailed inspection of fuselage frames at stations 360 and 380 for fatigue cracking. Applicable to Boeing 737-800 MSN 34xxx series.",
            ata_chapter="ATA 53", ata_description="Fuselage",
            scheduled_start=hm(-120), scheduled_end=hm(-112),
            actual_start=hm(-120), actual_end=hm(-114),
            lead_technician="Adel Fathalla (NDT Level III)", technicians=["Hossam Refaat"],
            hangar_bay="Hangar 1, Bay B",
            man_hours_est=12.0, man_hours_actual=6.0,
            ad_number="FAA AD 2024-09-12",
            work_order_ref="WO-2024-00815-AD",
            findings="No cracking found at FS360 and FS380. Eddy current and visual inspection results attached.",
            corrective_action="No corrective action required. Inspection result SERVICEABLE.",
            approved_by="Walid Abdel-Hamid", license_number="ECAR-AME-00445",
            sign_off_time=hm(-114),
        ),
    ]

    # ── MEL Items ──
    mel_items = [
        MELItem(
            aircraft_id=db_aircraft["SU-GEB"].id,
            mel_number="MEL-34-11-01B",
            ata_chapter="ATA 34", description="ACAS/TCAS II Resolution Advisory audio annunciation slightly degraded — visual RAs fully serviceable",
            category="C", dispatch_conditions="Dispatch permitted provided TCAS visual display fully serviceable and crew briefed. Repair within 10 calendar days.",
            raised_date="2024-10-10", expiry_date="2024-10-20",
            is_active=True, raised_by="Walid Abdel-Hamid",
        ),
        MELItem(
            aircraft_id=db_aircraft["SU-GEC"].id,
            mel_number="MEL-21-31-02A",
            ata_chapter="ATA 21", description="Row 18-22 overhead passenger reading light #2 inoperative",
            category="D", dispatch_conditions="Dispatch permitted. Affected passengers notified by crew. Repair within 120 calendar days.",
            raised_date="2024-09-15", expiry_date="2025-01-13",
            is_active=True, raised_by="Essam Khalil",
        ),
        MELItem(
            aircraft_id=db_aircraft["SU-GEE"].id,
            mel_number="MEL-31-51-01B",
            ata_chapter="ATA 31", description="Flight deck printer (ACARS printer) inoperative",
            category="B", dispatch_conditions="Dispatch permitted provided ACARS datalink is serviceable. Crew to use manual ATC communications backup. Repair within 3 calendar days.",
            raised_date="2024-10-18", expiry_date="2024-10-21",
            is_active=True, raised_by="Mazen El-Kady",
        ),
    ]

    # ── AOG Record ──
    aog_records = [
        AOGRecord(
            aircraft_id=db_aircraft["SU-GED"].id,
            aog_ref="AOG-2024-0089",
            status=AOGStatus.RECOVERING,
            location="CAI",
            fault_description="Green hydraulic system low pressure. Fatigue crack found in pressure line fitting P/N C20720-5100. Aircraft declared AOG on arrival. MNT task MNT-2024-00841 raised.",
            ata_chapter="ATA 29 — Hydraulic Power",
            grounded_at=datetime.now(timezone.utc) - timedelta(hours=3),
            affected_flights=["MS399 (cancelled)", "MS401 (now operated by SU-GEC)"],
            parts_on_order=["C20720-5100 — x2 — ETA 36h via Airbus AOG Centre Hamburg"],
            go_team_dispatched=False,
            estimated_tat="36-48 hours from now",
            notes="Part shipment confirmed. DHL airfreight from Hamburg. Estimated parts arrival 2024-10-22 08:00 UTC.",
        ),
    ]

    db.add_all(maint_logs)
    db.add_all(mel_items)
    db.add_all(aog_records)
    db.commit()
    print(f"  ✓ {len(maint_logs)} maintenance tasks, {len(mel_items)} MEL items, {len(aog_records)} AOG records")
