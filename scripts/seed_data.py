"""GRC Platform - Seed Data Script.

Populates the database with:
- NIST SP 800-53 framework
- 5 controls (PE-03, AC-02, SC-07, IR-06, RA-05)
- Required artifact types with percentage weightages
- Cross-framework mappings to NIST CSF 2.0, CIS Controls v8, PCI DSS v4.0.1
- Default admin user

Run after init_db.py:
    python scripts/seed_data.py
"""

import os
import uuid
from typing import Any, Optional

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# Data Definitions
# =============================================================================

FRAMEWORK_DATA = {
    "name": "NIST SP 800-53",
    "version": "Rev 5",
    "description": (
        "Security and Privacy Controls for Information Systems and Organizations. "
        "NIST SP 800-53 provides a catalog of security and privacy controls "
        "for federal information systems and organizations to protect "
        "against a diverse set of threats."
    ),
}

CONTROLS_DATA = [
    {
        "control_id": "PE-03",
        "title": "Physical Access Control",
        "description": (
            "Enforce physical access authorizations at facility entry and exit "
            "points by verifying individual access authorizations before granting "
            "access and controlling the flow of visitors. The organization shall: "
            "(a) Enforce physical access authorizations for all physical access "
            "points to the facility; (b) Verify individual access authorizations "
            "before granting access; (c) Control the flow of visitors through the "
            "facility; (d) Maintain physical access audit logs for a minimum of "
            "one year; and (e) Escort visitors and monitor visitor activity."
        ),
        "control_family": "Physical and Environmental Protection",
        "priority": "high",
        "artifact_requirements": [
            {"type": "Policy Documents", "weightage": 15.00,
             "description": "Physical security policy, access control policy"},
            {"type": "Procedures", "weightage": 15.00,
             "description": "Visitor access procedures, badge issuance procedures"},
            {"type": "Access Lists", "weightage": 20.00,
             "description": "Authorized personnel lists, role-based access matrices"},
            {"type": "System Configs", "weightage": 20.00,
             "description": "Badge reader configurations, access control system settings"},
            {"type": "Audit Logs", "weightage": 15.00,
             "description": "Access logs, entry/exit records, visitor logs"},
            {"type": "Training Records", "weightage": 5.00,
             "description": "Security awareness training for physical access"},
            {"type": "Inspection Reports", "weightage": 10.00,
             "description": "Physical security assessment reports"},
        ],
        "cross_framework_mappings": {
            "nist_csf_2_0": {
                "mapped_to": "PR.AA-06",
                "description": "Physical access to assets is managed, monitored, and enforced",
            },
            "cis_controls_v8": {
                "mapped_to": "CIS 6",
                "description": "Access Control Management",
            },
            "pci_dss_v4_0_1": {
                "mapped_to": "PCI 9.2 / 9.3",
                "description": "Physical access controls, badge systems",
            },
        },
    },
    {
        "control_id": "AC-02",
        "title": "Account Management",
        "description": (
            "Manage information system accounts including establishing, "
            "activating, modifying, reviewing, disabling, and removing accounts. "
            "The organization shall: (a) Establish and document account types; "
            "(b) Create accounts according to authorization; (c) Enable accounts "
            "according to organizational policies; (d) Review accounts at "
            "least quarterly; (e) Disable inactive accounts after 90 days; "
            "(f) Remove accounts upon termination or transfer; "
            "(g) Enforce least privilege and separation of duties."
        ),
        "control_family": "Access Control",
        "priority": "high",
        "artifact_requirements": [
            {"type": "Policy Documents", "weightage": 15.00,
             "description": "Account management policy, password policy"},
            {"type": "Procedures", "weightage": 15.00,
             "description": "Account creation/termination procedures"},
            {"type": "Account Inventories", "weightage": 20.00,
             "description": "Active account lists, service account registry"},
            {"type": "Access Reviews", "weightage": 20.00,
             "description": "Quarterly access review records, recertification logs"},
            {"type": "Configuration Records", "weightage": 15.00,
             "description": "IAM system configurations, MFA settings"},
            {"type": "Audit Logs", "weightage": 10.00,
             "description": "Account activity logs, privilege escalation logs"},
            {"type": "Training Records", "weightage": 5.00,
             "description": "Admin training documentation"},
        ],
        "cross_framework_mappings": {
            "nist_csf_2_0": {
                "mapped_to": "PR.AA-05",
                "description": "Identity management, authentication, and access control enforced",
            },
            "cis_controls_v8": {
                "mapped_to": "CIS 5 / CIS 6",
                "description": "Account Management / Access Control Management",
            },
            "pci_dss_v4_0_1": {
                "mapped_to": "PCI 2.2 / 7.2",
                "description": "System accounts, access assignment",
            },
        },
    },
    {
        "control_id": "SC-07",
        "title": "Boundary Protection",
        "description": (
            "Monitor and control communications at external managed interfaces "
            "to the system and at key internal managed interfaces within the "
            "system. The organization shall: (a) Define managed interfaces; "
            "(b) Implement subnetworks for publicly accessible system components; "
            "(c) Employ boundary protection devices; (d) Fail securely in the "
            "event of an operational failure; (e) Prevent unauthorized "
            "information transfer via shared resources."
        ),
        "control_family": "System and Communications Protection",
        "priority": "high",
        "artifact_requirements": [
            {"type": "Network Architecture", "weightage": 20.00,
             "description": "Network diagrams, DMZ configurations, VLAN layouts"},
            {"type": "Firewall Rules", "weightage": 25.00,
             "description": "Firewall rule sets, ACL configurations"},
            {"type": "Segmentation Policies", "weightage": 15.00,
             "description": "Network segmentation policies, microsegmentation rules"},
            {"type": "Monitoring Configs", "weightage": 15.00,
             "description": "IDS/IPS configurations, traffic monitoring setup"},
            {"type": "Audit Logs", "weightage": 15.00,
             "description": "Network traffic logs, blocked connection logs"},
            {"type": "Change Records", "weightage": 10.00,
             "description": "Firewall change tickets, network modification records"},
        ],
        "cross_framework_mappings": {
            "nist_csf_2_0": {
                "mapped_to": "PR.IR-01",
                "description": "Networks and environments are protected",
            },
            "cis_controls_v8": {
                "mapped_to": "CIS 13 / CIS 9",
                "description": "Network Monitoring and Defense / Email and Browser Protections",
            },
            "pci_dss_v4_0_1": {
                "mapped_to": "PCI 1.2 / 1.3",
                "description": "Firewall/network controls, DMZ",
            },
        },
    },
    {
        "control_id": "IR-06",
        "title": "Incident Reporting",
        "description": (
            "Require personnel to report suspected security incidents to the "
            "organizational incident response capability within organization-defined "
            "time period. The organization shall: (a) Require personnel to report "
            "security incidents within a defined time period; (b) Report incident "
            "information to designated authorities; (c) Provide incident reporting "
            "mechanisms and procedures; (d) Report incidents to external "
            "organizations as required by law or regulation."
        ),
        "control_family": "Incident Response",
        "priority": "high",
        "artifact_requirements": [
            {"type": "Policy Documents", "weightage": 15.00,
             "description": "Incident response policy, reporting procedures"},
            {"type": "IR Plan", "weightage": 20.00,
             "description": "Incident response plan, escalation procedures"},
            {"type": "Training Records", "weightage": 10.00,
             "description": "IR training materials, tabletop exercise records"},
            {"type": "Incident Records", "weightage": 25.00,
             "description": "Incident tickets, investigation reports"},
            {"type": "Communication Logs", "weightage": 15.00,
             "description": "Notification records, stakeholder communications"},
            {"type": "Lessons Learned", "weightage": 10.00,
             "description": "Post-incident reports, improvement action items"},
            {"type": "Contact Lists", "weightage": 5.00,
             "description": "Emergency contact lists, vendor contacts"},
        ],
        "cross_framework_mappings": {
            "nist_csf_2_0": {
                "mapped_to": "RS.CO-02",
                "description": "Incidents are reported to designated internal and external stakeholders",
            },
            "cis_controls_v8": {
                "mapped_to": "CIS 17",
                "description": "Incident Response Management",
            },
            "pci_dss_v4_0_1": {
                "mapped_to": "PCI 12.10",
                "description": "Incident response plan",
            },
        },
    },
    {
        "control_id": "RA-05",
        "title": "Vulnerability Scanning",
        "description": (
            "Scan for vulnerabilities in organizational information systems and "
            "information system components in organization-defined frequency. "
            "The organization shall: (a) Scan for vulnerabilities at least "
            "monthly; (b) Use appropriate scanning tools and techniques; "
            "(c) Analyze scan reports and remediate findings; "
            "(d) Share vulnerability information with relevant parties; "
            "(e) Update vulnerability scanning tools as new scans become available."
        ),
        "control_family": "Risk Assessment",
        "priority": "high",
        "artifact_requirements": [
            {"type": "Scanning Policies", "weightage": 15.00,
             "description": "Vulnerability scanning policy, scan scheduling policy"},
            {"type": "Tool Configurations", "weightage": 20.00,
             "description": "Scanner configs, scan profiles, credentialed scan settings"},
            {"type": "Scan Results", "weightage": 25.00,
             "description": "Vulnerability reports, scan output files"},
            {"type": "Remediation Records", "weightage": 20.00,
             "description": "Patch records, remediation tickets, exception approvals"},
            {"type": "Validation Reports", "weightage": 10.00,
             "description": "Rescan verification, false positive analysis"},
            {"type": "Metrics/Reports", "weightage": 10.00,
             "description": "Vulnerability trend reports, SLA compliance reports"},
        ],
        "cross_framework_mappings": {
            "nist_csf_2_0": {
                "mapped_to": "ID.RA-01",
                "description": "Vulnerabilities are identified, validated, and recorded",
            },
            "cis_controls_v8": {
                "mapped_to": "CIS 7",
                "description": "Continuous Vulnerability Management",
            },
            "pci_dss_v4_0_1": {
                "mapped_to": "PCI 11.3 / 6.3",
                "description": "External vulnerability scans / Secure development",
            },
        },
    },
]

DEFAULT_USER = {
    "username": "admin",
    "email": "admin@grc-platform.local",
    "full_name": "GRC Platform Administrator",
    "role": "admin",
}


# =============================================================================
# Database Operations
# =============================================================================

def get_connection() -> Any:
    """Create a database connection.

    Returns:
        psycopg2 connection object.

    Raises:
        Exception: If connection fails.
    """
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://grc_user:grc_pass@localhost:5432/grc_dev",
    )
    conn = psycopg2.connect(database_url)
    conn.autocommit = True
    return conn


def seed_framework(conn: Any) -> Optional[str]:
    """Insert the NIST SP 800-53 framework.

    Args:
        conn: Database connection.

    Returns:
        Framework ID as string, or None if skipped.
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Check if framework already exists
        cur.execute(
            "SELECT id FROM frameworks WHERE name = %s AND version = %s",
            (FRAMEWORK_DATA["name"], FRAMEWORK_DATA["version"]),
        )
        existing = cur.fetchone()
        if existing:
            print(f"  ⏭️  Framework '{FRAMEWORK_DATA['name']} {FRAMEWORK_DATA['version']}' already exists")
            return existing["id"]

        framework_id = str(uuid.uuid4())
        cur.execute(
            "INSERT INTO frameworks (id, name, version, description) "
            "VALUES (%s, %s, %s, %s)",
            (
                framework_id,
                FRAMEWORK_DATA["name"],
                FRAMEWORK_DATA["version"],
                FRAMEWORK_DATA["description"],
            ),
        )
        print(f"  ✓ Created framework: {FRAMEWORK_DATA['name']} {FRAMEWORK_DATA['version']}")
        return framework_id


def seed_controls(conn: Any, framework_id: str) -> list[str]:
    """Insert all 5 controls for the given framework.

    Args:
        conn: Database connection.
        framework_id: Framework UUID.

    Returns:
        List of control IDs that were inserted.
    """
    inserted_ids: list[str] = []

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        for control_data in CONTROLS_DATA:
            # Check if control already exists
            cur.execute(
                "SELECT id FROM controls WHERE framework_id = %s AND control_id = %s",
                (framework_id, control_data["control_id"]),
            )
            existing = cur.fetchone()
            if existing:
                print(
                    f"  ⏭️  Control '{control_data['control_id']}' "
                    f"({control_data['title']}) already exists"
                )
                inserted_ids.append(existing["id"])
                continue

            control_id = str(uuid.uuid4())
            cur.execute(
                "INSERT INTO controls (id, framework_id, control_id, title, "
                "description, control_family, priority, artifact_requirements, "
                "cross_framework_mappings) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb)",
                (
                    control_id,
                    framework_id,
                    control_data["control_id"],
                    control_data["title"],
                    control_data["description"],
                    control_data["control_family"],
                    control_data["priority"],
                    # Serialize artifact requirements to JSON
                    str(control_data["artifact_requirements"]).replace("'", '"'),
                    # Serialize cross-framework mappings to JSON
                    str(control_data["cross_framework_mappings"]).replace("'", '"'),
                ),
            )
            inserted_ids.append(control_id)

            # Calculate total weightage for verification
            total_weightage = sum(
                req["weightage"] for req in control_data["artifact_requirements"]
            )
            print(
                f"  ✓ Created control: {control_data['control_id']} - "
                f"{control_data['title']} "
                f"(Family: {control_data['control_family']}, "
                f"Weightages: {total_weightage:.0f}%)"
            )

            # Print cross-framework mappings
            mappings = control_data["cross_framework_mappings"]
            print(
                f"    Mappings: NIST CSF→{mappings['nist_csf_2_0']['mapped_to']}, "
                f"CIS→{mappings['cis_controls_v8']['mapped_to']}, "
                f"PCI DSS→{mappings['pci_dss_v4_0_1']['mapped_to']}"
            )

    return inserted_ids


def seed_default_user(conn: Any) -> Optional[str]:
    """Insert a default admin user.

    Args:
        conn: Database connection.

    Returns:
        User ID as string, or None if skipped.
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "SELECT id FROM users WHERE username = %s",
            (DEFAULT_USER["username"],),
        )
        existing = cur.fetchone()
        if existing:
            print(f"  ⏭️  User '{DEFAULT_USER['username']}' already exists")
            return existing["id"]

        user_id = str(uuid.uuid4())
        cur.execute(
            "INSERT INTO users (id, username, email, full_name, role) "
            "VALUES (%s, %s, %s, %s, %s)",
            (
                user_id,
                DEFAULT_USER["username"],
                DEFAULT_USER["email"],
                DEFAULT_USER["full_name"],
                DEFAULT_USER["role"],
            ),
        )
        print(f"  ✓ Created default user: {DEFAULT_USER['username']}")
        return user_id


def verify_seed_data(conn: Any) -> dict[str, Any]:
    """Verify that seed data was created correctly.

    Args:
        conn: Database connection.

    Returns:
        Dictionary with verification results.
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Count frameworks
        cur.execute("SELECT COUNT(*) as count FROM frameworks")
        framework_count = cur.fetchone()["count"]

        # Count controls
        cur.execute("SELECT COUNT(*) as count FROM controls")
        control_count = cur.fetchone()["count"]

        # Count users
        cur.execute("SELECT COUNT(*) as count FROM users")
        user_count = cur.fetchone()["count"]

        # Get control IDs for verification
        cur.execute(
            "SELECT control_id, title, control_family FROM controls "
            "ORDER BY control_id"
        )
        controls = cur.fetchall()

    print(f"\n  Frameworks: {framework_count}")
    print(f"  Controls: {control_count}")
    print(f"  Users: {user_count}")
    print(f"\n  Controls loaded:")
    for c in controls:
        print(f"    • {c['control_id']}: {c['title']} ({c['control_family']})")

    return {
        "frameworks": framework_count,
        "controls": control_count,
        "users": user_count,
    }


def main() -> None:
    """Main entry point for seeding the database."""
    print("=" * 50)
    print("  GRC Platform - Seed Data Loading")
    print("=" * 50)

    try:
        conn = get_connection()
        print("\nConnected to database successfully.\n")

        # Step 1: Create default user
        print("[1/4] Creating default user...")
        seed_default_user(conn)

        # Step 2: Create framework
        print("\n[2/4] Creating framework...")
        framework_id = seed_framework(conn)

        if framework_id is None:
            print("  ⚠️  Framework creation returned None")
            conn.close()
            return

        # Step 3: Create controls
        print("\n[3/4] Creating controls...")
        control_ids = seed_controls(conn, framework_id)
        print(f"\n  Total controls created: {len(control_ids)}")

        # Step 4: Verify
        print("\n[4/4] Verifying seed data...")
        result = verify_seed_data(conn)

        print("\n" + "=" * 50)
        if result["frameworks"] >= 1 and result["controls"] >= 5 and result["users"] >= 1:
            print("  ✅ Seed data loaded successfully!")
        else:
            print("  ⚠️  Some seed data may be incomplete")

        conn.close()

    except Exception as e:
        print(f"\n  ❌ Seed data loading failed: {e}")
        raise


if __name__ == "__main__":
    main()
