import uuid
import pandas as pd
import io
import csv
from datetime import datetime
from database import db


class TripService:
    """Core service for managing multiple group trips, advances, itemized expenses,
    flexible/weighted splitting, budget capping, and debt settlements.
    100% local with zero external APIs."""

    # ---------------------------------------------------------
    # TRIP CRUD
    # ---------------------------------------------------------
    @staticmethod
    def create_trip(user_id, name, description="", target_budget=0.0, start_date=None, end_date=None):
        trip_id = str(uuid.uuid4())
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        s_date = str(start_date) if start_date else str(datetime.now().date())
        e_date = str(end_date) if end_date else ""
        target_budget = float(target_budget or 0.0)

        db.execute(
            "INSERT INTO trips (id, user_id, name, description, target_budget, start_date, end_date, status, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?)",
            (trip_id, user_id, name.strip(), description.strip(), target_budget, s_date, e_date, now)
        )
        return trip_id

    @staticmethod
    def get_trips(user_id):
        """Get all trips for a user with member counts and total expenses."""
        query = """
            SELECT t.id, t.name, t.description, t.target_budget, t.start_date, t.end_date, t.status, t.created_at,
                   (SELECT COUNT(*) FROM trip_members WHERE trip_id = t.id) as member_count,
                   (SELECT COALESCE(SUM(amount), 0) FROM trip_expenses WHERE trip_id = t.id) as total_spent,
                   (SELECT COALESCE(SUM(amount), 0) FROM trip_advances WHERE trip_id = t.id) as total_advances
            FROM trips t
            WHERE t.user_id = ?
            ORDER BY (CASE WHEN t.status = 'active' THEN 0 ELSE 1 END), t.created_at DESC
        """
        res = db.execute(query, (user_id,))
        if res and res.rows:
            return pd.DataFrame(res.rows, columns=[
                "id", "name", "description", "target_budget", "start_date", "end_date",
                "status", "created_at", "member_count", "total_spent", "total_advances"
            ])
        return pd.DataFrame(columns=[
            "id", "name", "description", "target_budget", "start_date", "end_date",
            "status", "created_at", "member_count", "total_spent", "total_advances"
        ])

    @staticmethod
    def get_trip(trip_id):
        res = db.execute(
            "SELECT id, user_id, name, description, target_budget, start_date, end_date, status, created_at "
            "FROM trips WHERE id = ?",
            (trip_id,)
        )
        if res and res.rows:
            r = res.rows[0]
            return {
                "id": r[0], "user_id": r[1], "name": r[2], "description": r[3],
                "target_budget": float(r[4] or 0.0), "start_date": r[5],
                "end_date": r[6], "status": r[7], "created_at": r[8]
            }
        return None

    @staticmethod
    def update_trip_status(trip_id, status):
        db.execute("UPDATE trips SET status = ? WHERE id = ?", (status, trip_id))

    @staticmethod
    def update_trip(trip_id, name, description, target_budget, start_date, end_date):
        db.execute(
            "UPDATE trips SET name = ?, description = ?, target_budget = ?, start_date = ?, end_date = ? WHERE id = ?",
            (name.strip(), description.strip(), float(target_budget or 0.0), str(start_date), str(end_date), trip_id)
        )

    @staticmethod
    def delete_trip(trip_id, user_id):
        # Clean up related records
        db.execute("DELETE FROM trip_expense_splits WHERE expense_id IN (SELECT id FROM trip_expenses WHERE trip_id = ?)", (trip_id,))
        db.execute("DELETE FROM trip_expenses WHERE trip_id = ?", (trip_id,))
        db.execute("DELETE FROM trip_advances WHERE trip_id = ?", (trip_id,))
        db.execute("DELETE FROM trip_members WHERE trip_id = ?", (trip_id,))
        db.execute("DELETE FROM trips WHERE id = ? AND user_id = ?", (trip_id, user_id))

    # ---------------------------------------------------------
    # MEMBER OPERATIONS (Equal friends model)
    # ---------------------------------------------------------
    @staticmethod
    def add_member(trip_id, name, weight=1.0, max_budget=None):
        mid = str(uuid.uuid4())
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        w = float(weight if weight and weight > 0 else 1.0)
        mb = float(max_budget) if max_budget is not None and max_budget != "" and float(max_budget) > 0 else None

        db.execute(
            "INSERT INTO trip_members (id, trip_id, name, weight, max_budget, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (mid, trip_id, name.strip(), w, mb, now)
        )
        # Automatically rebalance all general expenses so new member is included
        TripService.rebalance_all_splits(trip_id)
        return mid

    @staticmethod
    def get_members(trip_id):
        res = db.execute(
            "SELECT id, name, weight, max_budget, created_at FROM trip_members WHERE trip_id = ? ORDER BY created_at ASC",
            (trip_id,)
        )
        if res and res.rows:
            return pd.DataFrame(res.rows, columns=["id", "name", "weight", "max_budget", "created_at"])
        return pd.DataFrame(columns=["id", "name", "weight", "max_budget", "created_at"])

    @staticmethod
    def update_member(member_id, name, weight=1.0, max_budget=None):
        res = db.execute("SELECT trip_id FROM trip_members WHERE id = ?", (member_id,))
        trip_id = res.rows[0][0] if res and res.rows else None
        w = float(weight if weight and weight > 0 else 1.0)
        mb = float(max_budget) if max_budget is not None and max_budget != "" and float(max_budget) > 0 else None
        db.execute(
            "UPDATE trip_members SET name = ?, weight = ?, max_budget = ? WHERE id = ?",
            (name.strip(), w, mb, member_id)
        )
        if trip_id:
            TripService.rebalance_all_splits(trip_id)

    @staticmethod
    def get_member_activity(member_id):
        """Get summary of expenses and advances paid by this friend for deletion safety checks."""
        res_m = db.execute("SELECT name, trip_id FROM trip_members WHERE id = ?", (member_id,))
        if not res_m or not res_m.rows:
            return None
        m_name, trip_id = res_m.rows[0]
        
        # Out-of-pocket expenses
        res_exp = db.execute("SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM trip_expenses WHERE payer_member_id = ?", (member_id,))
        exp_count = res_exp.rows[0][0] if res_exp and res_exp.rows else 0
        exp_total = float(res_exp.rows[0][1]) if res_exp and res_exp.rows else 0.0
        
        # Advances
        res_adv = db.execute("SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM trip_advances WHERE member_id = ?", (member_id,))
        adv_count = res_adv.rows[0][0] if res_adv and res_adv.rows else 0
        adv_total = float(res_adv.rows[0][1]) if res_adv and res_adv.rows else 0.0

        return {
            "name": m_name,
            "trip_id": trip_id,
            "expense_count": exp_count,
            "expense_total": exp_total,
            "advance_count": adv_count,
            "advance_total": adv_total,
            "total_spent": exp_total + adv_total
        }

    @staticmethod
    def delete_member(member_id):
        """Standard member deletion (delegates to reassignment with pool default)."""
        TripService.delete_member_with_reassignment(member_id, reassign_to_pool=True)

    @staticmethod
    def delete_member_with_reassignment(member_id, reassign_payer_id=None, reassign_to_pool=True, delete_expenses=False):
        """
        Delete a member with safe handling of their logged expenses and advances:
        - delete_expenses=True: Deletes expenses paid by this member.
        - reassign_to_pool=True: Marks expenses as paid from pool (shared by all friends).
        - reassign_payer_id: Assigns expenses to another friend.
        Also cleans up splits for this member and rebalances remaining members.
        """
        res = db.execute("SELECT trip_id FROM trip_members WHERE id = ?", (member_id,))
        if not res or not res.rows:
            return
        trip_id = res.rows[0][0]

        if delete_expenses:
            db.execute("DELETE FROM trip_expense_splits WHERE expense_id IN (SELECT id FROM trip_expenses WHERE payer_member_id = ?)", (member_id,))
            db.execute("DELETE FROM trip_expenses WHERE payer_member_id = ?", (member_id,))
            db.execute("DELETE FROM trip_advances WHERE member_id = ?", (member_id,))
        elif reassign_payer_id:
            db.execute("UPDATE trip_expenses SET payer_member_id = ?, paid_from_pool = 0 WHERE payer_member_id = ?", (reassign_payer_id, member_id))
            db.execute("UPDATE trip_advances SET member_id = ? WHERE member_id = ?", (reassign_payer_id, member_id))
        else: # reassign_to_pool (default)
            db.execute("UPDATE trip_expenses SET payer_member_id = NULL, paid_from_pool = 1 WHERE payer_member_id = ?", (member_id,))
            db.execute("DELETE FROM trip_advances WHERE member_id = ?", (member_id,))

        # Remove member's own split shares
        db.execute("DELETE FROM trip_expense_splits WHERE member_id = ?", (member_id,))
        # Delete the member
        db.execute("DELETE FROM trip_members WHERE id = ?", (member_id,))

        # Automatically rebalance all remaining splits across surviving friends
        if trip_id:
            TripService.rebalance_all_splits(trip_id)

    @staticmethod
    def rebalance_all_splits(trip_id):
        """
        Rebalances all equal/general expenses across all currently active trip friends.
        Ensures newly added friends or edited weights immediately reflect on all expenses.
        """
        members_df = TripService.get_members(trip_id)
        if members_df.empty:
            return

        res = db.execute("SELECT id, amount FROM trip_expenses WHERE trip_id = ? AND split_type = 'equal'", (trip_id,))
        if not res or not res.rows:
            return

        default_weights = {row['id']: float(row['weight'] or 1.0) for _, row in members_df.iterrows()}
        active_weights = {m_id: float(w) for m_id, w in default_weights.items() if float(w) > 0}
        total_w = sum(active_weights.values())

        if total_w <= 0:
            return

        member_list = list(active_weights.items())
        for exp_id, amt in res.rows:
            db.execute("DELETE FROM trip_expense_splits WHERE expense_id = ?", (exp_id,))
            allocated = 0.0
            float_amt = float(amt)
            for idx, (m_id, w) in enumerate(member_list):
                if idx == len(member_list) - 1:
                    share = round(float_amt - allocated, 2)
                else:
                    share = round(float_amt * (w / total_w), 2)
                    allocated += share
                db.execute(
                    "INSERT INTO trip_expense_splits (id, expense_id, member_id, weight, share_amount) VALUES (?, ?, ?, ?, ?)",
                    (str(uuid.uuid4()), exp_id, m_id, w, share)
                )

    # ---------------------------------------------------------
    # ADVANCES / POOL MONEY GIVEN
    # ---------------------------------------------------------
    @staticmethod
    def add_advance(trip_id, member_id, amount, description="", date=None):
        aid = str(uuid.uuid4())
        d = str(date) if date else str(datetime.now().date())
        db.execute(
            "INSERT INTO trip_advances (id, trip_id, member_id, amount, description, date) VALUES (?, ?, ?, ?, ?, ?)",
            (aid, trip_id, member_id, round(float(amount), 2), description.strip(), d)
        )
        return aid

    @staticmethod
    def get_advances(trip_id):
        query = """
            SELECT a.id, a.member_id, m.name as member_name, a.amount, a.description, a.date
            FROM trip_advances a
            JOIN trip_members m ON a.member_id = m.id
            WHERE a.trip_id = ?
            ORDER BY a.date DESC, a.id DESC
        """
        res = db.execute(query, (trip_id,))
        if res and res.rows:
            return pd.DataFrame(res.rows, columns=["id", "member_id", "member_name", "amount", "description", "date"])
        return pd.DataFrame(columns=["id", "member_id", "member_name", "amount", "description", "date"])

    @staticmethod
    def delete_advance(advance_id):
        db.execute("DELETE FROM trip_advances WHERE id = ?", (advance_id,))

    # ---------------------------------------------------------
    # EXPENSES & FLEXIBLE SPLITTING
    # ---------------------------------------------------------
    @staticmethod
    def add_expense(trip_id, payer_member_id, paid_from_pool, amount, description, date=None, split_type="equal", member_weights=None):
        """
        Add a labeled expense and generate split entries.
        - payer_member_id: member_id of the person who paid out-of-pocket (or None if paid_from_pool=True).
        - paid_from_pool: bool / int (1 if paid from pooled money, 0 if out-of-pocket by a friend).
        - member_weights: dict of {member_id: weight} indicating which members are included and their weight for this expense.
          If None, splits among ALL trip members according to their default weights.
        """
        eid = str(uuid.uuid4())
        d = str(date) if date else str(datetime.now().date())
        amt = round(float(amount), 2)
        is_pool = 1 if paid_from_pool else 0
        payer_id = None if is_pool else payer_member_id

        db.execute(
            "INSERT INTO trip_expenses (id, trip_id, payer_member_id, paid_from_pool, amount, description, date, split_type) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (eid, trip_id, payer_id, is_pool, amt, description.strip(), d, split_type)
        )

        # Get members to split among
        members_df = TripService.get_members(trip_id)
        if members_df.empty:
            return eid

        # Determine splits
        if not member_weights:
            member_weights = {row['id']: float(row['weight'] or 1.0) for _, row in members_df.iterrows()}

        active_weights = {m_id: float(w) for m_id, w in member_weights.items() if float(w) > 0}
        total_w = sum(active_weights.values())

        if total_w > 0:
            member_list = list(active_weights.items())
            allocated = 0.0
            for idx, (m_id, w) in enumerate(member_list):
                if idx == len(member_list) - 1:
                    share = round(amt - allocated, 2)
                else:
                    share = round(amt * (w / total_w), 2)
                    allocated += share
                db.execute(
                    "INSERT INTO trip_expense_splits (id, expense_id, member_id, weight, share_amount) VALUES (?, ?, ?, ?, ?)",
                    (str(uuid.uuid4()), eid, m_id, w, share)
                )

        return eid

    @staticmethod
    def get_expenses(trip_id):
        query = """
            SELECT e.id, e.payer_member_id, 
                   COALESCE(m.name, '💼 Pool Fund') as payer_name,
                   e.paid_from_pool, e.amount, e.description, e.date, e.split_type
            FROM trip_expenses e
            LEFT JOIN trip_members m ON e.payer_member_id = m.id
            WHERE e.trip_id = ?
            ORDER BY e.date DESC, e.id DESC
        """
        res = db.execute(query, (trip_id,))
        if res and res.rows:
            df = pd.DataFrame(res.rows, columns=[
                "id", "payer_member_id", "payer_name", "paid_from_pool", "amount", "description", "date", "split_type"
            ])
            splits_res = db.execute("""
                SELECT s.expense_id, m.name, s.share_amount
                FROM trip_expense_splits s
                JOIN trip_members m ON s.member_id = m.id
                WHERE s.expense_id IN (SELECT id FROM trip_expenses WHERE trip_id = ?)
            """, (trip_id,))
            
            splits_map = {}
            if splits_res and splits_res.rows:
                for exp_id, m_name, s_amt in splits_res.rows:
                    if exp_id not in splits_map:
                        splits_map[exp_id] = []
                    splits_map[exp_id].append(f"{m_name}: ₹{float(s_amt):,.0f}")
            
            df['splits_summary'] = df['id'].apply(lambda x: ", ".join(splits_map.get(x, [])))
            return df
        return pd.DataFrame(columns=[
            "id", "payer_member_id", "payer_name", "paid_from_pool", "amount", "description", "date", "split_type", "splits_summary"
        ])

    @staticmethod
    def delete_expense(expense_id):
        db.execute("DELETE FROM trip_expense_splits WHERE expense_id = ?", (expense_id,))
        db.execute("DELETE FROM trip_expenses WHERE id = ?", (expense_id,))

    # ---------------------------------------------------------
    # SETTLEMENT LEDGER & RECORDING
    # ---------------------------------------------------------
    @staticmethod
    def record_settlement(trip_id, from_name, to_name, amount):
        """Record a completed settlement payment."""
        sid = str(uuid.uuid4())
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        amt = round(float(amount), 2)
        if amt > 0:
            db.execute(
                "INSERT INTO trip_settlements (id, trip_id, from_name, to_name, amount, settled_at) VALUES (?, ?, ?, ?, ?, ?)",
                (sid, trip_id, from_name.strip(), to_name.strip(), amt, now)
            )
        return sid

    @staticmethod
    def get_settlements(trip_id):
        """Get all recorded settlement payments for this trip."""
        res = db.execute(
            "SELECT id, trip_id, from_name, to_name, amount, settled_at FROM trip_settlements WHERE trip_id = ? ORDER BY settled_at DESC",
            (trip_id,)
        )
        if res and res.rows:
            return pd.DataFrame(res.rows, columns=["id", "trip_id", "from_name", "to_name", "amount", "settled_at"])
        return pd.DataFrame(columns=["id", "trip_id", "from_name", "to_name", "amount", "settled_at"])

    @staticmethod
    def delete_settlement(settlement_id):
        """Revert or delete a recorded settlement."""
        db.execute("DELETE FROM trip_settlements WHERE id = ?", (settlement_id,))

    # ---------------------------------------------------------
    # SETTLEMENT & RECONCILIATION ENGINE
    # ---------------------------------------------------------
    @staticmethod
    def calculate_trip_summary(trip_id):
        """
        Comprehensive calculation of:
        - Total expenses, total advances, pool cash in hand.
        - Target budget vs. actual spend.
        - Per-member: advances given, out-of-pocket paid, total paid, base share, capped share, net balance.
        - L1 Budget Deficit Detection.
        - Simplified Settle-Up transaction plan with live 'Paid' tracking.
        """
        trip = TripService.get_trip(trip_id)
        if not trip:
            return None

        members_df = TripService.get_members(trip_id)
        advances_df = TripService.get_advances(trip_id)
        expenses_df = TripService.get_expenses(trip_id)

        # Totals with rounding polish
        total_spent = round(float(expenses_df['amount'].sum()), 2) if not expenses_df.empty else 0.0
        total_advances = round(float(advances_df['amount'].sum()), 2) if not advances_df.empty else 0.0
        
        pool_expenses = round(float(expenses_df[expenses_df['paid_from_pool'] == 1]['amount'].sum()), 2) if not expenses_df.empty else 0.0
        direct_expenses = round(float(expenses_df[expenses_df['paid_from_pool'] == 0]['amount'].sum()), 2) if not expenses_df.empty else 0.0
        
        # Current Cash in Hand from pool
        pool_cash_in_hand = round(max(0.0, total_advances - pool_expenses), 2)

        # Target budget tracking
        target_budget = round(trip['target_budget'], 2)
        remaining_budget = round(max(0.0, target_budget - total_spent), 2) if target_budget > 0 else 0.0
        burn_pct = min(1.0, total_spent / target_budget) if target_budget > 0 else 0.0

        if members_df.empty:
            return {
                "trip": trip,
                "members": [],
                "total_spent": total_spent,
                "total_advances": total_advances,
                "pool_expenses": pool_expenses,
                "direct_expenses": direct_expenses,
                "pool_cash_in_hand": pool_cash_in_hand,
                "target_budget": target_budget,
                "remaining_budget": remaining_budget,
                "burn_pct": burn_pct,
                "has_cap_deficit": False,
                "deficit_amount": 0.0,
                "settlements": [],
                "is_all_settled": True,
                "member_summary": []
            }

        # Calculate per-member contributions and base shares
        # 1. Base shares from expense splits
        splits_query = """
            SELECT s.member_id, SUM(s.share_amount) as total_share
            FROM trip_expense_splits s
            JOIN trip_expenses e ON s.expense_id = e.id
            WHERE e.trip_id = ?
            GROUP BY s.member_id
        """
        splits_res = db.execute(splits_query, (trip_id,))
        base_shares = {}
        if splits_res and splits_res.rows:
            for m_id, sh in splits_res.rows:
                base_shares[m_id] = round(float(sh or 0.0), 2)

        # 2. Advances per member
        member_advances = {}
        if not advances_df.empty:
            for m_id, grp in advances_df.groupby('member_id'):
                member_advances[m_id] = round(float(grp['amount'].sum()), 2)

        # 3. Out-of-pocket expenses per member
        member_direct = {}
        if not expenses_df.empty:
            direct_df = expenses_df[expenses_df['paid_from_pool'] == 0]
            for m_id, grp in direct_df.groupby('payer_member_id'):
                if m_id:
                    member_direct[m_id] = round(float(grp['amount'].sum()), 2)

        # Initialize member structures
        members_data = []
        for _, row in members_df.iterrows():
            m_id = row['id']
            m_name = row['name']
            m_weight = float(row['weight'] or 1.0)
            m_max = float(row['max_budget']) if pd.notnull(row['max_budget']) and row['max_budget'] is not None else None
            
            adv = member_advances.get(m_id, 0.0)
            oop = member_direct.get(m_id, 0.0)
            tot_paid = round(adv + oop, 2)
            b_share = base_shares.get(m_id, 0.0)

            members_data.append({
                "id": m_id,
                "name": m_name,
                "weight": m_weight,
                "max_budget": m_max,
                "advance_given": adv,
                "out_of_pocket": oop,
                "total_paid": tot_paid,
                "base_share": b_share,
                "final_share": b_share,
                "is_capped": False,
                "overflow_absorbed": 0.0
            })

        # 4. Apply Budget Limit / Cap Overflow Redistribution
        max_iterations = 10
        for _ in range(max_iterations):
            overflow_to_redistribute = 0.0
            uncapped_members = []

            for m in members_data:
                if m['max_budget'] is not None and m['final_share'] > m['max_budget']:
                    overflow_to_redistribute += (m['final_share'] - m['max_budget'])
                    m['final_share'] = m['max_budget']
                    m['is_capped'] = True
                elif m['max_budget'] is None or m['final_share'] < m['max_budget']:
                    uncapped_members.append(m)

            if overflow_to_redistribute <= 0.01 or not uncapped_members:
                break

            total_uncapped_weight = sum(m['weight'] for m in uncapped_members)
            if total_uncapped_weight <= 0:
                break

            uncapped_allocated = 0.0
            for idx, m in enumerate(uncapped_members):
                if idx == len(uncapped_members) - 1:
                    share_of_overflow = round(overflow_to_redistribute - uncapped_allocated, 2)
                else:
                    share_of_overflow = round(overflow_to_redistribute * (m['weight'] / total_uncapped_weight), 2)
                    uncapped_allocated += share_of_overflow
                m['final_share'] = round(m['final_share'] + share_of_overflow, 2)
                m['overflow_absorbed'] = round(m['overflow_absorbed'] + share_of_overflow, 2)

        # Check for L1 (Limit Deficit): If all members have caps and sum(caps) < total_spent
        all_capped = len(members_data) > 0 and all(m['max_budget'] is not None for m in members_data)
        sum_caps = sum((m['max_budget'] or 0.0) for m in members_data)
        has_cap_deficit = all_capped and (sum_caps < (total_spent - 0.01))
        deficit_amount = round(max(0.0, total_spent - sum_caps), 2) if has_cap_deficit else 0.0

        # 5. Compute Net Balances with subtle rounding polish
        for m in members_data:
            m['final_share'] = round(m['final_share'], 2)
            m['total_paid'] = round(m['total_paid'], 2)
            m['net_balance'] = round(m['total_paid'] - m['final_share'], 2)
            if abs(m['net_balance']) < 0.005:
                m['net_balance'] = 0.0
                m['status'] = 'settled'
            elif m['net_balance'] > 0.005:
                m['status'] = 'refund'
            else:
                m['status'] = 'owes'

        # 6. Simplified Settle-Up Algorithm
        debtors = []
        creditors = []

        for m in members_data:
            bal = m['net_balance']
            if bal < -0.01:
                debtors.append({'name': m['name'], 'amount': -bal})
            elif bal > 0.01:
                creditors.append({'name': m['name'], 'amount': bal})

        net_pool_balance = round(total_advances - pool_expenses, 2)
        if net_pool_balance > 0.01:
            debtors.append({'name': '💼 Pool Cash (In Hand)', 'amount': net_pool_balance})
        elif net_pool_balance < -0.01:
            creditors.append({'name': '💼 Pool Fund (Reimburse)', 'amount': -net_pool_balance})

        debtors.sort(key=lambda x: x['amount'], reverse=True)
        creditors.sort(key=lambda x: x['amount'], reverse=True)

        # Query recorded settlements from database
        settlements_df = TripService.get_settlements(trip_id)
        paid_map = {}
        if not settlements_df.empty:
            for _, sr in settlements_df.iterrows():
                key = (sr['from_name'].strip(), sr['to_name'].strip())
                paid_map[key] = paid_map.get(key, 0.0) + float(sr['amount'])

        # Compute per-member settlements paid and received, and update current balance
        for m in members_data:
            m_name_clean = m['name'].strip()
            paid_by_m = sum(float(sr['amount']) for _, sr in settlements_df.iterrows() if sr['from_name'].strip() == m_name_clean) if not settlements_df.empty else 0.0
            received_by_m = sum(float(sr['amount']) for _, sr in settlements_df.iterrows() if sr['to_name'].strip() == m_name_clean) if not settlements_df.empty else 0.0
            
            m['settlements_paid'] = round(paid_by_m, 2)
            m['settlements_received'] = round(received_by_m, 2)

            init_bal = m['net_balance']
            if init_bal < -0.005: # Member originally owed money
                orig_debt = -init_bal
                rem_debt = round(max(0.0, orig_debt - paid_by_m), 2)
                m['remaining_balance'] = -rem_debt
                m['current_status'] = 'settled' if rem_debt <= 0.005 else 'owes'
            elif init_bal > 0.005: # Member originally was owed a refund
                orig_refund = init_bal
                rem_refund = round(max(0.0, orig_refund - received_by_m), 2)
                m['remaining_balance'] = rem_refund
                m['current_status'] = 'settled' if rem_refund <= 0.005 else 'refund'
            else:
                m['remaining_balance'] = 0.0
                m['current_status'] = 'settled'

        # Pool cash in hand remaining after disbursements
        pool_cash_disbursed = sum(float(sr['amount']) for _, sr in settlements_df.iterrows() if "Pool Cash" in sr['from_name']) if not settlements_df.empty else 0.0
        remaining_pool_cash = round(max(0.0, pool_cash_in_hand - pool_cash_disbursed), 2)

        settlements = []
        d_idx, c_idx = 0, 0

        while d_idx < len(debtors) and c_idx < len(creditors):
            d = debtors[d_idx]
            c = creditors[c_idx]

            settle_amt = round(min(d['amount'], c['amount']), 2)
            if settle_amt > 0.01:
                key = (d['name'].strip(), c['name'].strip())
                already_paid = paid_map.get(key, 0.0)
                
                transfer_paid = round(min(already_paid, settle_amt), 2)
                paid_map[key] = max(0.0, already_paid - transfer_paid)
                
                rem_amt = round(max(0.0, settle_amt - transfer_paid), 2)
                is_paid = rem_amt <= 0.01
                
                is_pool_cash = ("Pool Cash" in d['name'] or "Pool Fund" in d['name'] or "Pool Fund" in c['name'])
                transfer_type = "pool_cash" if is_pool_cash else "friend_transfer"

                settlements.append({
                    "from_name": d['name'],
                    "to_name": c['name'],
                    "amount": settle_amt,
                    "paid_amount": transfer_paid,
                    "remaining_amount": rem_amt,
                    "is_paid": is_paid,
                    "transfer_type": transfer_type
                })

            d['amount'] -= settle_amt
            c['amount'] -= settle_amt

            if d['amount'] <= 0.01:
                d_idx += 1
            if c['amount'] <= 0.01:
                c_idx += 1

        is_all_settled = (len(settlements) == 0) or all(s['is_paid'] for s in settlements) or all(m['current_status'] == 'settled' for m in members_data)

        return {
            "trip": trip,
            "members": members_data,
            "total_spent": total_spent,
            "total_advances": total_advances,
            "pool_expenses": pool_expenses,
            "direct_expenses": direct_expenses,
            "pool_cash_in_hand": pool_cash_in_hand,
            "remaining_pool_cash": remaining_pool_cash,
            "target_budget": target_budget,
            "remaining_budget": remaining_budget,
            "burn_pct": burn_pct,
            "has_cap_deficit": has_cap_deficit,
            "deficit_amount": deficit_amount,
            "settlements": settlements,
            "is_all_settled": is_all_settled,
            "member_summary": members_data
        }

    # ---------------------------------------------------------
    # LOCAL WHATSAPP SUMMARY GENERATOR (Zero APIs)
    # ---------------------------------------------------------
    @staticmethod
    def generate_whatsapp_summary(trip_id, currency_sym="₹"):
        summary = TripService.calculate_trip_summary(trip_id)
        if not summary:
            return "No trip data found."

        trip = summary['trip']
        members = summary['members']
        settlements = summary['settlements']

        total_members = len(members)
        avg_share = (summary['total_spent'] / total_members) if total_members > 0 else 0.0

        lines = [
            f"🌴 *{trip['name']} - Trip Settlement Summary*",
            f"📅 Dates: {trip['start_date']}" + (f" to {trip['end_date']}" if trip['end_date'] else ""),
            f"💰 *Total Trip Spend:* {currency_sym}{summary['total_spent']:,.2f}",
        ]

        if summary['target_budget'] > 0:
            lines.append(f"🎯 *Target Budget:* {currency_sym}{summary['target_budget']:,.2f} (Remaining: {currency_sym}{summary['remaining_budget']:,.2f})")

        lines.append(f"👥 *Avg Cost / Head:* {currency_sym}{avg_share:,.2f}")
        lines.append("")
        lines.append("📊 *Individual Member Breakdown:*")

        for m in members:
            status_text = ""
            if m.get('current_status') == 'refund' and m.get('remaining_balance', 0.0) > 0.01:
                status_text = f"➡️ *Gets Refund: {currency_sym}{m['remaining_balance']:,.2f}* 🟢"
            elif m.get('current_status') == 'owes' and m.get('remaining_balance', 0.0) < -0.01:
                status_text = f"➡️ *Owes: {currency_sym}{-m['remaining_balance']:,.2f}* 🔴"
            else:
                status_text = f"➡️ *All Settled* ✅"

            cap_info = f" (Capped at {currency_sym}{m['max_budget']:,.0f})" if m['is_capped'] else ""
            weight_info = f" [{m['weight']}x]" if m['weight'] != 1.0 else ""
            
            lines.append(f"• *{m['name']}*{weight_info}: Paid {currency_sym}{m['total_paid']:,.2f} | Share {currency_sym}{m['final_share']:,.2f}{cap_info} {status_text}")

        lines.append("")
        lines.append("🤝 *Simplified Settle-Up Plan:*")
        if not settlements:
            lines.append("🎉 All accounts are fully settled! No transfers needed.")
        else:
            for s in settlements:
                badge = "[💼 Cash in Hand] " if s['transfer_type'] == 'pool_cash' else ""
                paid_str = " ✅ *[PAID]*" if s['is_paid'] else " ⏳ *[PENDING]*"
                lines.append(f"👉 {badge}*{s['from_name']}* pays *{s['to_name']}* {currency_sym}{s['amount']:,.2f}{paid_str}")

        lines.append("")
        lines.append("✨ _Generated via WealthFlow Pro_")
        return "\n".join(lines)

    # ---------------------------------------------------------
    # LOCAL CSV EXPORT (Zero APIs)
    # ---------------------------------------------------------
    @staticmethod
    def get_trip_csv_data(trip_id, currency_sym="₹"):
        summary = TripService.calculate_trip_summary(trip_id)
        if not summary:
            return ""

        trip = summary['trip']
        members = summary['members']
        expenses_df = TripService.get_expenses(trip_id)
        advances_df = TripService.get_advances(trip_id)
        settlements_df = TripService.get_settlements(trip_id)

        output = io.StringIO()
        writer = csv.writer(output)

        # Section 1: Trip Overview
        writer.writerow(["=== TRIP OVERVIEW ==="])
        writer.writerow(["Trip Name", trip['name']])
        writer.writerow(["Status", trip['status'].upper()])
        writer.writerow(["Start Date", trip['start_date']])
        writer.writerow(["End Date", trip['end_date'] or "N/A"])
        writer.writerow(["Total Spent", f"{summary['total_spent']:.2f}"])
        writer.writerow(["Target Budget", f"{summary['target_budget']:.2f}"])
        writer.writerow(["Remaining Budget", f"{summary['remaining_budget']:.2f}"])
        writer.writerow(["Total Advances Collected", f"{summary['total_advances']:.2f}"])
        writer.writerow(["Pool Expenses", f"{summary['pool_expenses']:.2f}"])
        writer.writerow(["Pool Cash in Hand", f"{summary['pool_cash_in_hand']:.2f}"])
        writer.writerow([])

        # Section 2: Member Settlement Summary
        writer.writerow(["=== MEMBER SETTLEMENT SUMMARY ==="])
        writer.writerow(["Member Name", "Weight", "Budget Cap", "Advances Given", "Out of Pocket", "Total Paid", "Final Share", "Net Balance", "Settlements Paid", "Settlements Received", "Remaining Balance", "Current Status"])
        for m in members:
            writer.writerow([
                m['name'],
                f"{m['weight']}x",
                f"{m['max_budget']:.2f}" if m['max_budget'] else "None",
                f"{m['advance_given']:.2f}",
                f"{m['out_of_pocket']:.2f}",
                f"{m['total_paid']:.2f}",
                f"{m['final_share']:.2f}",
                f"{m['net_balance']:.2f}",
                f"{m['settlements_paid']:.2f}",
                f"{m['settlements_received']:.2f}",
                f"{m['remaining_balance']:.2f}",
                "All Settled" if m['current_status'] == 'settled' else ("Gets Refund" if m['current_status'] == 'refund' else "Owes")
            ])
        writer.writerow([])

        # Section 3: Settle-Up Transactions
        writer.writerow(["=== SIMPLIFIED SETTLE-UP TRANSFERS ==="])
        writer.writerow(["From (Payer)", "To (Receiver)", "Amount", "Status"])
        for s in summary['settlements']:
            status_tag = "PAID" if s['is_paid'] else "PENDING"
            writer.writerow([s['from_name'], s['to_name'], f"{s['amount']:.2f}", status_tag])
        writer.writerow([])

        # Section 4: Itemized Expenses
        writer.writerow(["=== ITEMIZED EXPENSE LEDGER ==="])
        writer.writerow(["Date", "Description", "Amount", "Paid By", "Split Details"])
        if not expenses_df.empty:
            for _, r in expenses_df.iterrows():
                writer.writerow([r['date'], r['description'], f"{r['amount']:.2f}", r['payer_name'], r['splits_summary']])
        writer.writerow([])

        # Section 5: Advances Ledger
        writer.writerow(["=== ADVANCES / POOL CONTRIBUTIONS ==="])
        writer.writerow(["Date", "Member", "Amount", "Description"])
        if not advances_df.empty:
            for _, r in advances_df.iterrows():
                writer.writerow([r['date'], r['member_name'], f"{r['amount']:.2f}", r['description']])
        writer.writerow([])

        # Section 6: Recorded Settlement Payments
        writer.writerow(["=== COMPLETED SETTLEMENT PAYMENTS ==="])
        writer.writerow(["Settled At", "From", "To", "Amount"])
        if not settlements_df.empty:
            for _, r in settlements_df.iterrows():
                writer.writerow([r['settled_at'], r['from_name'], r['to_name'], f"{r['amount']:.2f}"])

        return output.getvalue()

