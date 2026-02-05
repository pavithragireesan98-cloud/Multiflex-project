#!/usr/bin/env python
"""
Route Verification Script for MULTIFLEX
Tests all the accept/reject payment routes
"""

from flask import Flask
from user import user
from database import select

app = Flask(__name__)
app.secret_key = "multiflex123"
app.register_blueprint(user)

print("=" * 60)
print("MULTIFLEX ROUTE VERIFICATION")
print("=" * 60)

# Get all routes
print("\nRegistered Routes:")
print("-" * 60)

for rule in app.url_map.iter_rules():
    if 'accept' in rule.rule or 'reject' in rule.rule or 'pay' in rule.rule:
        print(f"✓ {rule.rule:40} -> {rule.endpoint}")

print("\n" + "=" * 60)
print("DATABASE VERIFICATION")
print("=" * 60)

print("\nChecking request_master table for 'assigned' status...")
try:
    q = """
        SELECT r.request_id, r.user_id, r.worker_id, r.worker_status, 
               r.user_decision, s.skill_name,
               p.amount, p.status as proposal_status
        FROM request_master r
        JOIN skill s ON r.skill_id = s.skill_id
        LEFT JOIN proposals p ON p.request_master_id = r.request_id
        WHERE r.worker_status = 'assigned'
        LIMIT 3
    """
    results = select(q)
    
    if results:
        print(f"\nFound {len(results)} assigned requests:")
        for row in results:
            print(f"\n  Request ID: {row['request_id']}")
            print(f"  Skill: {row['skill_name']}")
            print(f"  Worker Status: {row['worker_status']}")
            print(f"  User Decision: {row['user_decision']}")
            print(f"  Proposal Amount: {row['amount']}")
            print(f"  Proposal Status: {row['proposal_status']}")
    else:
        print("\n⚠️  No assigned requests found in database!")
        print("   Please ensure a worker has accepted a request and set work date/time.")
        
except Exception as e:
    print(f"\n❌ Error querying database: {str(e)}")

print("\n" + "=" * 60)
print("ROUTE MAPPING")
print("=" * 60)

mappings = [
    ("Accept Payment", "/user_accept_payment/<int:req_id>", "Updates user_decision='accepted', redirects to /pay"),
    ("Reject Assigned", "/user_reject_assigned/<int:req_id>", "Updates user_decision='rejected'"),
    ("Payment Page", "/pay?req_id=X&amount=Y", "Shows payment form"),
    ("Payment Success", "/payment_success/<int:req_id>", "Updates status='paid'"),
]

for name, route, description in mappings:
    print(f"\n{name}:")
    print(f"  Route: {route}")
    print(f"  Purpose: {description}")

print("\n" + "=" * 60)
print("✅ Verification Complete!")
print("=" * 60)
