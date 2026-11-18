import uuid
import pandas as pd
import streamlit as st
from database import db


@st.cache_data(ttl=60, show_spinner=False)
def _cached_goals(user_id: str, v: int):
    res = db.execute(
        "SELECT id, name, target_amount, current_amount, deadline, icon FROM goals WHERE user_id = ?", (user_id,)
    )
    cols = ["id", "Name", "Target", "Current", "Deadline", "Icon"]
    if res and res.rows:
        return pd.DataFrame(res.rows, columns=cols)
    return pd.DataFrame(columns=cols)


class GoalService:
    """Piggy-bank savings tracker with custom emoji support."""

    @staticmethod
    def get_goals(user_id):
        return _cached_goals(user_id, db.version)

    @staticmethod
    def add_goal(user_id, name, target, deadline, icon="🎯"):
        gid = str(uuid.uuid4())
        db.execute(
            "INSERT INTO goals (id, user_id, name, target_amount, current_amount, deadline, icon) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (gid, user_id, name, target, 0.0, str(deadline), icon),
        )

    @staticmethod
    def contribute(goal_id, amount):
        db.execute(
            "UPDATE goals SET current_amount = current_amount + ? WHERE id = ?",
            (amount, goal_id),
        )

    @staticmethod
    def delete_goal(goal_id, user_id):
        db.execute("DELETE FROM goals WHERE id = ? AND user_id = ?", (goal_id, user_id))
