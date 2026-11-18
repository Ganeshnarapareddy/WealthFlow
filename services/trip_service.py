import uuid
import pandas as pd
import io
import csv
from datetime import datetime
import streamlit as st
from database import db


@st.cache_data(ttl=60, show_spinner=False)
def _cached_get_trips(user_id: str, v: int):
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
    cols = [
        "id", "name", "description", "target_budget", "start_date", "end_date",
        "status", "created_at", "member_count", "total_spent", "total_advances"
    ]
    if res and res.rows:
        return pd.DataFrame(res.rows, columns=cols)
    return pd.DataFrame(columns=cols)


@st.cache_data(ttl=60, show_spinner=False)
def _cached_trip_bundle(trip_id: str, v: int):
    """Fetch ALL data for a trip (metadata, members, advances, expenses, splits, settlements)
    in ONE SINGLE Turso HTTP roundtrip and compute summary + member activity in memory."""
    results = db.batch([
        (
            "SELECT id, user_id, name, description, target_budget, start_date, end_date, status, created_at "
            "FROM trips WHERE id = ?",
            (trip_id,),
        ),
        (
            "SELECT id, name, weight, max_budget, created_at FROM trip_members "
            "WHERE trip_id = ? ORDER BY created_at ASC",
            (trip_id,),
        ),
        (
            "SELECT a.id, a.member_id, m.name as member_name, a.amount, a.description, a.date "
            "FROM trip_advances a JOIN trip_members m ON a.member_id = m.id "
            "WHERE a.trip_id = ? ORDER BY a.date DESC, a.id DESC",
            (trip_id,),
        ),
        (
            "SELECT e.id, e.payer_member_id, COALESCE(m.name, '💼 Pool Fund') as payer_name, "
            "e.paid_from_pool, e.amount, e.description, e.date, e.split_type "
            "FROM trip_expenses e LEFT JOIN trip_members m ON e.payer_member_id = m.id "
            "WHERE e.trip_id = ? ORDER BY e.date DESC, e.id DESC",
            (trip_id,),
        ),
        (
            "SELECT s.expense_id, s.member_id, m.name, s.share_amount "
            "FROM trip_expense_splits s JOIN trip_members m ON s.member_id = m.id "
            "WHERE s.expense_id IN (SELECT id FROM trip_expenses WHERE trip_id = ?)",
            (trip_id,),
        ),
        (
            "SELECT id, trip_id, from_name, to_name, amount, settled_at "
            "FROM trip_settlements WHERE trip_id = ? ORDER BY settled_at DESC",
            (trip_id,),
        ),
    ])

    res_trip, res_members, res_adv, res_exp, res_splits, res_settle = results

    if not res_trip or not res_trip.rows:
        return None

    r = res_trip.rows[0]
    trip = {
        "id": r[0], "user_id": r[1], "name": r[2], "description": r[3],
        "target_budget": float(r[4] or 0.0), "start_date": r[5],
        "end_date": r[6], "status": r[7], "created_at": r[8]
    }

    members_df = (
        pd.DataFrame(res_members.rows, columns=["id", "name", "weight", "max_budget", "created_at"])
        if res_members and res_members.rows
        else pd.DataFrame(columns=["id", "name", "weight", "max_budget", "created_at"])
    )

    advances_df = (
        pd.DataFrame(res_adv.rows, columns=["id", "member_id", "member_name", "amount", "description", "date"])
        if res_adv and res_adv.rows
        else pd.DataFrame(columns=["id", "member_id", "member_name", "amount", "description", "date"])
    )

    # Build splits_summary per expense AND base_shares per member in one pass
    splits_map = {}
    base_shares = {}
    if res_splits and res_splits.rows:
        for exp_id, m_id, m_name, s_amt in res_splits.rows:
            s_val = float(s_amt or 0.0)
            splits_map.setdefault(exp_id, []).append(f"{m_name}: ₹{s_val:,.0f}")
            base_shares[m_id] = base_shares.get(m_id, 0.0) + s_val
    base_shares = {k: round(v, 2) for k, v in base_shares.items()}

    if res_exp and res_exp.rows:
        expenses_df = pd.DataFrame(res_exp.rows, columns=[
            "id", "payer_member_id", "payer_name", "paid_from_pool", "amount", "description", "date", "split_type"
        ])
        expenses_df["splits_summary"] = expenses_df["id"].apply(lambda x: ", ".join(splits_map.get(x, [])))
    else:
        expenses_df = pd.DataFrame(columns=[
            "id", "payer_member_id", "payer_name", "paid_from_pool", "amount", "description", "date", "split_type", "splits_summary"
        ])

    settlements_df = (
        pd.DataFrame(res_settle.rows, columns=["id", "trip_id", "from_name", "to_name", "amount", "settled_at"])
        if res_settle and res_settle.rows
        else pd.DataFrame(columns=["id", "trip_id", "from_name", "to_name", "amount", "settled_at"])
    )

    # Precompute member activity in memory (eliminates N*3 queries on Friends tab)
    member_activity = {}
    if not members_df.empty:
        exp_counts = {}
        exp_totals = {}
        if not expenses_df.empty:
            for m_id, grp in expenses_df.groupby("payer_member_id"):
                if m_id:
                    exp_counts[m_id] = int(len(grp))
                    exp_totals[m_id] = round(float(grp["amount"].sum()), 2)
        adv_counts = {}
        adv_totals = {}
        if not advances_df.empty:
            for m_id, grp in advances_df.groupby("member_id"):
                if m_id:
                    adv_counts[m_id] = int(len(grp))
                    adv_totals[m_id] = round(float(grp["amount"].sum()), 2)
        for _, row in members_df.iterrows():
            mid = row["id"]
            et = exp_totals.get(mid, 0.0)
            at = adv_totals.get(mid, 0.0)
            member_activity[mid] = {
                "name": row["name"],
                "trip_id": trip_id,
                "expense_count": exp_counts.get(mid, 0),
                "expense_total": et,
                "advance_count": adv_counts.get(mid, 0),
                "advance_total": at,
                "total_spent": round(et + at, 2),
            }

    summary = TripService._compute_summary_from_frames(
        trip, members_df, advances_df, expenses_df, base_shares, settlements_df
    )

    return {
        "trip": trip,
        "members_df": members_df,
        "advances_df": advances_df,
        "expenses_df": expenses_df,
        "settlements_df": settlements_df,
        "member_activity": member_activity,
        "summary": summary,
    }


class TripService:
    """Core service for managing multiple group trips, advances, itemized expenses,
    flexible/weighted splitting, budget capping, and debt settlements.
    100% local with zero external APIs — bulk-batched for low-latency Turso access."""

    # ---------------------------------------------------------
    # BULK FETCH
    # ---------------------------------------------------------
    @staticmethod
    def get_trip_bundle(trip_id):
        """Return cached bulk bundle with trip, members_df, advances_df, expenses_df,
        settlements_df, member_activity, and summary in 1 DB roundtrip."""
        return _cached_trip_bundle(trip_id, db.version)

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
    def create_trip_with_creator(user_id, name, creator_name, description="", target_budget=0.0, start_date=None, end_date=None):
        """Create trip and add creator as first member in a single DB roundtrip."""
        trip_id = str(uuid.uuid4())
        mid = str(uuid.uuid4())
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        s_date = str(start_date) if start_date else str(datetime.now().date())
        e_date = str(end_date) if end_date else ""
        target_budget = float(target_budget or 0.0)

        db.batch([
            (
                "INSERT INTO trips (id, user_id, name, description, target_budget, start_date, end_date, status, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?)",
                (trip_id, user_id, name.strip(), description.strip(), target_budget, s_date, e_date, now),
            ),
            (
                "INSERT INTO trip_members (id, trip_id, name, weight, max_budget, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (mid, trip_id, creator_name.strip(), 1.0, None, now),
            ),
        ])
        return trip_id

    @staticmethod
    def get_trips(user_id):
        """Get all trips for a user with member counts and total expenses."""
        return _cached_get_trips(user_id, db.version)

    @staticmethod
    def get_trip(trip_id):
        bundle = TripService.get_trip_bundle(trip_id)
        return bundle["trip"] if bundle else None

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
        # Clean up all related records in ONE single batch roundtrip
        db.batch([
            ("DELETE FROM trip_expense_splits WHERE expense_id IN (SELECT id FROM trip_expenses WHERE trip_id = ?)", (trip_id,)),
            ("DELETE FROM trip_expenses WHERE trip_id = ?", (trip_id,)),
            ("DELETE FROM trip_advances WHERE trip_id = ?", (trip_id,)),
            ("DELETE FROM trip_settlements WHERE trip_id = ?", (trip_id,)),
            ("DELETE FROM trip_members WHERE trip_id = ?", (trip_id,)),
            ("DELETE FROM trips WHERE id = ? AND user_id = ?", (trip_id, user_id)),
        ])

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
        # Automatically rebalance all general expenses in 1 batched roundtrip
        TripService.rebalance_all_splits(trip_id)
        return mid

    @staticmethod
    def get_members(trip_id):
        bundle = TripService.get_trip_bundle(trip_id)
        if bundle:
            return bundle["members_df"]
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
        results = db.batch([
            ("SELECT name, trip_id FROM trip_members WHERE id = ?", (member_id,)),
            ("SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM trip_expenses WHERE payer_member_id = ?", (member_id,)),
            ("SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM trip_advances WHERE member_id = ?", (member_id,)),
        ])
        res_m, res_exp, res_adv = results
        if not res_m or not res_m.rows:
            return None
        m_name, trip_id = res_m.rows[0]
        exp_count = res_exp.rows[0][0] if res_exp and res_exp.rows else 0
        exp_total = float(res_exp.rows[0][1]) if res_exp and res_exp.rows else 0.0
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
        Delete a member with safe handling of their logged expenses and advances in a single batch.
        """
        res = db.execute("SELECT trip_id FROM trip_members WHERE id = ?", (member_id,))
        if not res or not res.rows:
            return
        trip_id = res.rows[0][0]

        stmts = []
        if delete_expenses:
            stmts.append(("DELETE FROM trip_expense_splits WHERE expense_id IN (SELECT id FROM trip_expenses WHERE payer_member_id = ?)", (member_id,)))
            stmts.append(("DELETE FROM trip_expenses WHERE payer_member_id = ?", (member_id,)))
            stmts.append(("DELETE FROM trip_advances WHERE member_id = ?", (member_id,)))
        elif reassign_payer_id:
            stmts.append(("UPDATE trip_expenses SET payer_member_id = ?, paid_from_pool = 0 WHERE payer_member_id = ?", (reassign_payer_id, member_id)))
            stmts.append(("UPDATE trip_advances SET member_id = ? WHERE member_id = ?", (reassign_payer_id, member_id)))
        else:  # reassign_to_pool (default)
            stmts.append(("UPDATE trip_expenses SET payer_member_id = NULL, paid_from_pool = 1 WHERE payer_member_id = ?", (member_id,)))
            stmts.append(("DELETE FROM trip_advances WHERE member_id = ?", (member_id,)))

        stmts.append(("DELETE FROM trip_expense_splits WHERE member_id = ?", (member_id,)))
        stmts.append(("DELETE FROM trip_members WHERE id = ?", (member_id,)))
        db.batch(stmts)

        if trip_id:
            TripService.rebalance_all_splits(trip_id)

    @staticmethod
    def rebalance_all_splits(trip_id):
        """
        Rebalances all equal/general expenses across all currently active trip friends
        using bulk batched queries (2 HTTP calls total regardless of expense/member count).
        """
        res_m, res_exp = db.batch([
            ("SELECT id, weight FROM trip_members WHERE trip_id = ? ORDER BY created_at ASC", (trip_id,)),
            ("SELECT id, amount FROM trip_expenses WHERE trip_id = ? AND split_type = 'equal'", (trip_id,)),
        ])
        if not res_m or not res_m.rows or not res_exp or not res_exp.rows:
            return

        active_weights = {row[0]: float(row[1] or 1.0) for row in res_m.rows if float(row[1] or 1.0) > 0}
        total_w = sum(active_weights.values())
        if total_w <= 0:
            return

        member_list = list(active_weights.items())
        write_stmts = []
        for exp_id, amt in res_exp.rows:
            write_stmts.append(("DELETE FROM trip_expense_splits WHERE expense_id = ?", (exp_id,)))
            allocated = 0.0
            float_amt = float(amt)
            for idx, (m_id, w) in enumerate(member_list):
                if idx == len(member_list) - 1:
                    share = round(float_amt - allocated, 2)
                else:
                    share = round(float_amt * (w / total_w), 2)
                    allocated += share
                write_stmts.append((
                    "INSERT INTO trip_expense_splits (id, expense_id, member_id, weight, share_amount) VALUES (?, ?, ?, ?, ?)",
                    (str(uuid.uuid4()), exp_id, m_id, w, share),
                ))

        if write_stmts:
            db.batch(write_stmts)

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
        bundle = TripService.get_trip_bundle(trip_id)
        if bundle:
            return bundle["advances_df"]
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
        Add a labeled expense and all split entries in ONE single batched Turso HTTP roundtrip.
        """
        eid = str(uuid.uuid4())
        d = str(date) if date else str(datetime.now().date())
        amt = round(float(amount), 2)
        is_pool = 1 if paid_from_pool else 0
        payer_id = None if is_pool else payer_member_id

        stmts = [(
            "INSERT INTO trip_expenses (id, trip_id, payer_member_id, paid_from_pool, amount, description, date, split_type) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (eid, trip_id, payer_id, is_pool, amt, description.strip(), d, split_type),
        )]

        # Only fetch members if caller did not supply member_weights
        if not member_weights:
            members_df = TripService.get_members(trip_id)
            if not members_df.empty:
                member_weights = {row['id']: float(row['weight'] or 1.0) for _, row in members_df.iterrows()}
            else:
                member_weights = {}

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
                stmts.append((
                    "INSERT INTO trip_expense_splits (id, expense_id, member_id, weight, share_amount) VALUES (?, ?, ?, ?, ?)",
                    (str(uuid.uuid4()), eid, m_id, w, share),
                ))

        db.batch(stmts)
        return eid

    @staticmethod
    def get_expenses(trip_id):
        bundle = TripService.get_trip_bundle(trip_id)
        if bundle:
            return bundle["expenses_df"]
        return pd.DataFrame(columns=[
            "id", "payer_member_id", "payer_name", "paid_from_pool", "amount", "description", "date", "split_type", "splits_summary"
        ])

    @staticmethod
    def delete_expense(expense_id):
        db.batch([
            ("DELETE FROM trip_expense_splits WHERE expense_id = ?", (expense_id,)),
            ("DELETE FROM trip_expenses WHERE id = ?", (expense_id,)),
        ])

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
        bundle = TripService.get_trip_bundle(trip_id)
        if bundle:
            return bundle["settlements_df"]
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
        bundle = TripService.get_trip_bundle(trip_id)
        return bundle["summary"] if bundle else None

    @staticmethod
    def _compute_summary_from_frames(trip, members_df, advances_df, expenses_df, base_shares, settlements_df):
        total_spent = round(float(expenses_df['amount'].sum()), 2) if not expenses_df.empty else 0.0
        total_advances = round(float(advances_df['amount'].sum()), 2) if not advances_df.empty else 0.0

        pool_expenses = round(float(expenses_df[expenses_df['paid_from_pool'] == 1]['amount'].sum()), 2) if not expenses_df.empty else 0.0
        direct_expenses = round(float(expenses_df[expenses_df['paid_from_pool'] == 0]['amount'].sum()), 2) if not expenses_df.empty else 0.0

        pool_cash_in_hand = round(max(0.0, total_advances - pool_expenses), 2)

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
                "remaining_pool_cash": pool_cash_in_hand,
                "target_budget": target_budget,
                "remaining_budget": remaining_budget,
                "burn_pct": burn_pct,
                "has_cap_deficit": False,
                "deficit_amount": 0.0,
                "settlements": [],
                "is_all_settled": True,
                "member_summary": []
            }

        # Advances per member
        member_advances = {}
        if not advances_df.empty:
            for m_id, grp in advances_df.groupby('member_id'):
                member_advances[m_id] = round(float(grp['amount'].sum()), 2)

        # Out-of-pocket expenses per member
        member_direct = {}
        if not expenses_df.empty:
            direct_df = expenses_df[expenses_df['paid_from_pool'] == 0]
            for m_id, grp in direct_df.groupby('payer_member_id'):
                if m_id:
                    member_direct[m_id] = round(float(grp['amount'].sum()), 2)

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

        # Apply Budget Limit / Cap Overflow Redistribution
        for _ in range(10):
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

        all_capped = len(members_data) > 0 and all(m['max_budget'] is not None for m in members_data)
        sum_caps = sum((m['max_budget'] or 0.0) for m in members_data)
        has_cap_deficit = all_capped and (sum_caps < (total_spent - 0.01))
        deficit_amount = round(max(0.0, total_spent - sum_caps), 2) if has_cap_deficit else 0.0

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

        paid_map = {}
        if not settlements_df.empty:
            for _, sr in settlements_df.iterrows():
                key = (sr['from_name'].strip(), sr['to_name'].strip())
                paid_map[key] = paid_map.get(key, 0.0) + float(sr['amount'])

        for m in members_data:
            m_name_clean = m['name'].strip()
            paid_by_m = sum(float(sr['amount']) for _, sr in settlements_df.iterrows() if sr['from_name'].strip() == m_name_clean) if not settlements_df.empty else 0.0
            received_by_m = sum(float(sr['amount']) for _, sr in settlements_df.iterrows() if sr['to_name'].strip() == m_name_clean) if not settlements_df.empty else 0.0

            m['settlements_paid'] = round(paid_by_m, 2)
            m['settlements_received'] = round(received_by_m, 2)

            init_bal = m['net_balance']
            if init_bal < -0.005:
                orig_debt = -init_bal
                rem_debt = round(max(0.0, orig_debt - paid_by_m), 2)
                m['remaining_balance'] = -rem_debt
                m['current_status'] = 'settled' if rem_debt <= 0.005 else 'owes'
            elif init_bal > 0.005:
                orig_refund = init_bal
                rem_refund = round(max(0.0, orig_refund - received_by_m), 2)
                m['remaining_balance'] = rem_refund
                m['current_status'] = 'settled' if rem_refund <= 0.005 else 'refund'
            else:
                m['remaining_balance'] = 0.0
                m['current_status'] = 'settled'

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
    # LOCAL WHATSAPP SUMMARY GENERATOR (Zero APIs, Zero extra DB calls)
    # ---------------------------------------------------------
    @staticmethod
    def generate_whatsapp_summary(trip_id, currency_sym="₹", bundle=None):
        b = bundle or TripService.get_trip_bundle(trip_id)
        summary = b["summary"] if b else None
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
    # LOCAL CSV EXPORT (Zero APIs, Zero extra DB calls)
    # ---------------------------------------------------------
    @staticmethod
    def get_trip_csv_data(trip_id, currency_sym="₹", bundle=None):
        b = bundle or TripService.get_trip_bundle(trip_id)
        if not b or not b.get("summary"):
            return ""

        summary = b["summary"]
        trip = summary['trip']
        members = summary['members']
        expenses_df = b["expenses_df"]
        advances_df = b["advances_df"]
        settlements_df = b["settlements_df"]

        output = io.StringIO()
        writer = csv.writer(output)

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

        writer.writerow(["=== SIMPLIFIED SETTLE-UP TRANSFERS ==="])
        writer.writerow(["From (Payer)", "To (Receiver)", "Amount", "Status"])
        for s in summary['settlements']:
            status_tag = "PAID" if s['is_paid'] else "PENDING"
            writer.writerow([s['from_name'], s['to_name'], f"{s['amount']:.2f}", status_tag])
        writer.writerow([])

        writer.writerow(["=== ITEMIZED EXPENSE LEDGER ==="])
        writer.writerow(["Date", "Description", "Amount", "Paid By", "Split Details"])
        if not expenses_df.empty:
            for _, r in expenses_df.iterrows():
                writer.writerow([r['date'], r['description'], f"{r['amount']:.2f}", r['payer_name'], r['splits_summary']])
        writer.writerow([])

        writer.writerow(["=== ADVANCES / POOL CONTRIBUTIONS ==="])
        writer.writerow(["Date", "Member", "Amount", "Description"])
        if not advances_df.empty:
            for _, r in advances_df.iterrows():
                writer.writerow([r['date'], r['member_name'], f"{r['amount']:.2f}", r['description']])
        writer.writerow([])

        writer.writerow(["=== COMPLETED SETTLEMENT PAYMENTS ==="])
        writer.writerow(["Settled At", "From", "To", "Amount"])
        if not settlements_df.empty:
            for _, r in settlements_df.iterrows():
                writer.writerow([r['settled_at'], r['from_name'], r['to_name'], f"{r['amount']:.2f}"])

        return output.getvalue()
