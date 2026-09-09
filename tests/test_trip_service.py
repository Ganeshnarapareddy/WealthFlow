import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from database import db
from services.trip_service import TripService

def test_trip_splitter_math():
    print("--- RUNNING TRIP SPLITTER MATHEMATICAL VERIFICATION ---")
    
    # 1. Create a test trip
    test_user_id = "test_user_trip_unit"
    trip_id = TripService.create_trip(
        user_id=test_user_id,
        name="Pune Weekend Trip",
        description="Trip with friends Ganesh, Bharat, Omsi",
        target_budget=25000.0,
        start_date="2026-09-10",
        end_date="2026-09-12"
    )
    print(f"Created Test Trip: {trip_id}")

    # 2. Add members
    m_ganesh = TripService.add_member(trip_id, "Ganesh", weight=1.0)
    m_bharat = TripService.add_member(trip_id, "Bharat", weight=1.0)
    m_omsi = TripService.add_member(trip_id, "Omsi", weight=1.0, max_budget=5000.0)
    print("Added members: Ganesh (1x), Bharat (1x), Omsi (1x, cap ₹5000)")

    # 3. Add advances (Total advances = ₹18,000 to cover ₹18,000 pool expenses)
    TripService.add_advance(trip_id, m_ganesh, 5500.0, "Initial Pool Transfer")
    TripService.add_advance(trip_id, m_bharat, 6500.0, "Initial Pool Transfer")
    TripService.add_advance(trip_id, m_omsi, 6000.0, "Initial Pool Transfer")
    print("Recorded Advances: Ganesh: ₹5,500 | Bharat: ₹6,500 | Omsi: ₹6,000 (Total: ₹18,000)")

    # 4. Add labeled expenses
    TripService.add_expense(trip_id, m_ganesh, paid_from_pool=False, amount=150.0, description="Auto to Station", date="2026-09-10")
    TripService.add_expense(trip_id, m_bharat, paid_from_pool=False, amount=100.0, description="Bikes Rental", date="2026-09-10")
    TripService.add_expense(trip_id, None, paid_from_pool=True, amount=6000.0, description="Resort Stay", date="2026-09-11")
    TripService.add_expense(trip_id, None, paid_from_pool=True, amount=12000.0, description="Food & Activities", date="2026-09-12")
    print("Recorded 4 Labeled Expenses (Total spend: ₹18,250)")

    # 5. Calculate summary
    summary = TripService.calculate_trip_summary(trip_id)
    assert summary is not None, "Summary calculation failed"

    print("\n--- SUMMARY METRICS ---")
    print(f"Total Spent: ₹{summary['total_spent']:,.2f}")
    print(f"Total Advances: ₹{summary['total_advances']:,.2f}")
    print(f"Pool Expenses: ₹{summary['pool_expenses']:,.2f}")
    print(f"Direct Expenses: ₹{summary['direct_expenses']:,.2f}")
    print(f"Pool Cash in Hand: ₹{summary['pool_cash_in_hand']:,.2f}")
    print(f"Target Budget: ₹{summary['target_budget']:,.2f} | Remaining: ₹{summary['remaining_budget']:,.2f}")

    assert summary['total_spent'] == 18250.0, f"Expected 18250, got {summary['total_spent']}"
    assert summary['total_advances'] == 18000.0, f"Expected 18000, got {summary['total_advances']}"
    assert summary['pool_expenses'] == 18000.0, f"Expected 18000, got {summary['pool_expenses']}"
    assert summary['direct_expenses'] == 250.0, f"Expected 250, got {summary['direct_expenses']}"

    print("\n--- MEMBER BREAKDOWN ---")
    total_final_shares = 0.0
    total_net_balances = 0.0

    for m in summary['members']:
        print(f"• {m['name']}: Total Paid=₹{m['total_paid']:,.2f} (Adv: ₹{m['advance_given']:,.2f} + Direct: ₹{m['out_of_pocket']:,.2f}) | "
              f"Base Share=₹{m['base_share']:,.2f} | Final Share=₹{m['final_share']:,.2f} (Capped: {m['is_capped']}) | "
              f"Net Balance=₹{m['net_balance']:,.2f} ({m['status'].upper()})")
        total_final_shares += m['final_share']
        total_net_balances += m['net_balance']

        if m['name'] == "Omsi":
            assert m['is_capped'] is True, "Omsi should be capped"
            assert abs(m['final_share'] - 5000.0) < 0.01, f"Omsi final share should be 5000, got {m['final_share']}"
            assert abs(m['net_balance'] - 1000.0) < 0.01, f"Omsi should get ₹1000 refund (Paid 6k - 5k share), got {m['net_balance']}"
        elif m['name'] == "Ganesh":
            assert abs(m['final_share'] - 6625.0) < 0.01, f"Ganesh final share should be 6625, got {m['final_share']}"
            assert abs(m['net_balance'] - (-975.0)) < 0.01, f"Ganesh owes 975, got {m['net_balance']}"
        elif m['name'] == "Bharat":
            assert abs(m['final_share'] - 6625.0) < 0.01, f"Bharat final share should be 6625, got {m['final_share']}"
            assert abs(m['net_balance'] - (-25.0)) < 0.01, f"Bharat owes 25, got {m['net_balance']}"

    assert abs(total_final_shares - summary['total_spent']) < 0.01, f"Sum of shares ({total_final_shares}) != Total spent ({summary['total_spent']})"
    assert abs(total_net_balances) < 0.01, f"Net balances do not sum to 0: {total_net_balances}"

    print("\n--- SIMPLIFIED SETTLE-UP TRANSFERS ---")
    for s in summary['settlements']:
        print(f"👉 {s['from_name']} pays {s['to_name']} ₹{s['amount']:,.2f}")

    # 6. Test WhatsApp Summary
    wa_text = TripService.generate_whatsapp_summary(trip_id)
    print("\n--- WHATSAPP SUMMARY PREVIEW ---")
    print(wa_text)
    assert "Pune Weekend Trip" in wa_text
    assert "Omsi" in wa_text
    assert "Bharat" in wa_text
    assert "Ganesh" in wa_text

    # 7. Test CSV export
    csv_text = TripService.get_trip_csv_data(trip_id)
    assert "=== TRIP OVERVIEW ===" in csv_text
    assert "=== MEMBER SETTLEMENT SUMMARY ===" in csv_text
    assert "=== ITEMIZED EXPENSE LEDGER ===" in csv_text
    print("\nCSV Export validation passed!")

def test_weighted_couples_split():
    print("\n--- RUNNING WEIGHTED / COUPLES SPLIT TEST ---")
    test_user_id = "test_user_couples_unit"
    trip_id = TripService.create_trip(test_user_id, "Goa Roadtrip", target_budget=30000.0)

    # 3 friends: Single (1x), Single (1x), Couple (2x) -> Total weight = 4.0
    m_single1 = TripService.add_member(trip_id, "Alice", weight=1.0)
    m_single2 = TripService.add_member(trip_id, "Bob", weight=1.0)
    m_couple = TripService.add_member(trip_id, "Charlie & Dana", weight=2.0)

    # Single1 pays ₹4,000 for dinner for everyone
    TripService.add_expense(trip_id, m_single1, paid_from_pool=False, amount=4000.0, description="Seafood Dinner")

    summary = TripService.calculate_trip_summary(trip_id)
    assert summary is not None

    for m in summary['members']:
        if m['name'] == "Alice":
            assert abs(m['final_share'] - 1000.0) < 0.01, f"Alice share should be 1000, got {m['final_share']}"
            assert abs(m['net_balance'] - 3000.0) < 0.01, f"Alice gets 3000 refund, got {m['net_balance']}"
        elif m['name'] == "Bob":
            assert abs(m['final_share'] - 1000.0) < 0.01, f"Bob share should be 1000, got {m['final_share']}"
            assert abs(m['net_balance'] - (-1000.0)) < 0.01, f"Bob owes 1000, got {m['net_balance']}"
        elif m['name'] == "Charlie & Dana":
            assert abs(m['final_share'] - 2000.0) < 0.01, f"Couple share should be 2000 (2x), got {m['final_share']}"
            assert abs(m['net_balance'] - (-2000.0)) < 0.01, f"Couple owes 2000, got {m['net_balance']}"

def test_pool_cash_settlement():
    print("\n--- RUNNING POOL CASH SETTLE-UP TEST ---")
    test_user_id = "test_user_pool_unit"
    trip_id = TripService.create_trip(test_user_id, "Pune Trip", target_budget=20000.0)

    # 5 Friends: Ganesh, Bharat, Vamsi, Shashank, Test User (2x, cap 2000)
    m_ganesh = TripService.add_member(trip_id, "Ganesh", weight=1.0)
    m_bharat = TripService.add_member(trip_id, "Bharat", weight=1.0)
    m_vamsi = TripService.add_member(trip_id, "Vamsi", weight=1.0)
    m_shashank = TripService.add_member(trip_id, "Shashank", weight=1.0)
    m_test = TripService.add_member(trip_id, "Test User", weight=2.0, max_budget=2000.0)

    # Advances
    TripService.add_advance(trip_id, m_bharat, 6750.0, "Advance")
    TripService.add_advance(trip_id, m_shashank, 1000.0, "Advance")

    # Out of pocket
    TripService.add_expense(trip_id, m_bharat, paid_from_pool=False, amount=100.0, description="Tolls")
    TripService.add_expense(trip_id, m_shashank, paid_from_pool=False, amount=10000.0, description="Resort Booking")
    TripService.add_expense(trip_id, None, paid_from_pool=True, amount=300.0, description="Snacks from Pool")

    summary = TripService.calculate_trip_summary(trip_id)
    assert summary is not None

    print("\nSettle-Up Plan with Pool Cash in Hand:")
    for s in summary['settlements']:
        print(f"👉 {s['from_name']} pays {s['to_name']} ₹{s['amount']:,.2f}")

    # Verify both Bharat and Shashank receive settlements
    receivers = {s['to_name'] for s in summary['settlements']}
    assert "Bharat" in receivers, "Bharat must be paid in the settle-up plan!"
    assert "Shashank" in receivers, "Shashank must be paid in the settle-up plan!"

    # Verify total received equals total refunds owed
    total_refunds = sum(s['amount'] for s in summary['settlements'])
    expected_refunds = sum(m['net_balance'] for m in summary['members'] if m['net_balance'] > 0.01)
    assert abs(total_refunds - expected_refunds) < 0.05, f"Expected {expected_refunds} refunds, got {total_refunds}"

    print("Pool Cash Settle-Up verified! Both Bharat and Shashank are 100% reimbursed! ✅")
    TripService.delete_trip(trip_id, test_user_id)

def test_settlements_and_is_paid():
    print("\n--- RUNNING SETTLEMENTS & 'PAID' ACTION TEST ---")
    test_user_id = "test_user_settle_unit"
    trip_id = TripService.create_trip(test_user_id, "Settlement Test Trip", target_budget=10000.0)

    m1 = TripService.add_member(trip_id, "Ganesh", weight=1.0)
    m2 = TripService.add_member(trip_id, "Shashank", weight=1.0)

    # Ganesh pays ₹0, Shashank pays ₹2,000 for dinner for both
    TripService.add_expense(trip_id, m2, paid_from_pool=False, amount=2000.0, description="Dinner")

    summary = TripService.calculate_trip_summary(trip_id)
    assert len(summary['settlements']) == 1
    transfer = summary['settlements'][0]
    assert transfer['from_name'] == "Ganesh"
    assert transfer['to_name'] == "Shashank"
    assert transfer['amount'] == 1000.0
    assert transfer['is_paid'] is False
    assert summary['is_all_settled'] is False

    # Ganesh pays Shashank ₹1,000 (clicks 'Paid')
    sid = TripService.record_settlement(trip_id, "Ganesh", "Shashank", 1000.0)
    assert sid is not None

    # Recalculate summary
    summary_after = TripService.calculate_trip_summary(trip_id)
    assert len(summary_after['settlements']) == 1
    transfer_after = summary_after['settlements'][0]
    assert transfer_after['is_paid'] is True
    assert transfer_after['remaining_amount'] == 0.0
    assert summary_after['is_all_settled'] is True

    # Verify each member's remaining balance is 0.0 and status is 'settled'
    for m in summary_after['members']:
        assert m['current_status'] == 'settled', f"{m['name']} should be settled, got {m['current_status']}"
        assert m['remaining_balance'] == 0.0, f"{m['name']} remaining balance should be 0, got {m['remaining_balance']}"

    # Verify WhatsApp summary shows 'All Settled' for all members
    wa_text = TripService.generate_whatsapp_summary(trip_id)
    assert "• *Ganesh*: Paid ₹0.00 | Share ₹1,000.00 ➡️ *All Settled* ✅" in wa_text
    assert "• *Shashank*: Paid ₹2,000.00 | Share ₹1,000.00 ➡️ *All Settled* ✅" in wa_text

    # Check settlements ledger
    df_settle = TripService.get_settlements(trip_id)
    assert len(df_settle) == 1
    assert df_settle.iloc[0]['from_name'] == "Ganesh"
    assert df_settle.iloc[0]['to_name'] == "Shashank"
    assert df_settle.iloc[0]['amount'] == 1000.0

    # Delete settlement
    TripService.delete_settlement(sid)
    summary_reverted = TripService.calculate_trip_summary(trip_id)
    assert summary_reverted['settlements'][0]['is_paid'] is False
    assert summary_reverted['is_all_settled'] is False

    print("Settlements and 'Paid' action tracking verified! ✅")
    TripService.delete_trip(trip_id, test_user_id)

def test_member_deletion_safety_and_reassignment():
    print("\n--- RUNNING MEMBER DELETION SAFETY & REASSIGNMENT TEST ---")
    test_user_id = "test_user_del_unit"
    trip_id = TripService.create_trip(test_user_id, "Deletion Safety Trip")

    m_alice = TripService.add_member(trip_id, "Alice", weight=1.0)
    m_bob = TripService.add_member(trip_id, "Bob", weight=1.0)
    m_test = TripService.add_member(trip_id, "Test User", weight=1.0)

    # Test User pays ₹1,000 out of pocket and ₹500 advance
    TripService.add_advance(trip_id, m_test, 500.0, "Test User Pool Cash")
    TripService.add_expense(trip_id, m_test, paid_from_pool=False, amount=1000.0, description="Cab fare")

    # Check activity
    activity = TripService.get_member_activity(m_test)
    assert activity['expense_count'] == 1
    assert activity['expense_total'] == 1000.0
    assert activity['advance_count'] == 1
    assert activity['advance_total'] == 500.0

    # Test 1: Reassign to Pool Fund (default)
    TripService.delete_member_with_reassignment(m_test, reassign_to_pool=True)

    # Verify expenses are now paid_from_pool = 1
    expenses = TripService.get_expenses(trip_id)
    assert len(expenses) == 1
    assert expenses.iloc[0]['paid_from_pool'] == 1
    assert expenses.iloc[0]['payer_name'] == "💼 Pool Fund"

    # Verify remaining members are Alice and Bob, each bearing ₹500 share
    summary = TripService.calculate_trip_summary(trip_id)
    assert len(summary['members']) == 2
    for m in summary['members']:
        assert abs(m['final_share'] - 500.0) < 0.01

    print("Member deletion safety with expense reassignment verified! ✅")
    TripService.delete_trip(trip_id, test_user_id)

def test_l1_cap_deficit():
    print("\n--- RUNNING L1 BUDGET CAP DEFICIT TEST ---")
    test_user_id = "test_user_l1_unit"
    trip_id = TripService.create_trip(test_user_id, "L1 Deficit Trip")

    # 2 members, each capped at ₹1,000 (total caps = ₹2,000)
    m1 = TripService.add_member(trip_id, "Person A", weight=1.0, max_budget=1000.0)
    m2 = TripService.add_member(trip_id, "Person B", weight=1.0, max_budget=1000.0)

    # Total spend is ₹3,000 (deficit = ₹1,000)
    TripService.add_expense(trip_id, m1, paid_from_pool=False, amount=3000.0, description="Expensive Luxury Stay")

    summary = TripService.calculate_trip_summary(trip_id)
    assert summary['has_cap_deficit'] is True
    assert abs(summary['deficit_amount'] - 1000.0) < 0.01
    print(f"L1 Deficit detected correctly: Deficit amount = ₹{summary['deficit_amount']} ✅")

    TripService.delete_trip(trip_id, test_user_id)

if __name__ == "__main__":
    test_trip_splitter_math()
    test_weighted_couples_split()
    test_pool_cash_settlement()
    test_settlements_and_is_paid()
    test_member_deletion_safety_and_reassignment()
    test_l1_cap_deficit()

