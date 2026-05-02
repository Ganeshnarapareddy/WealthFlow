import uuid
import pandas as pd
from database import db


class GoalService:
    """Piggy-bank savings tracker with custom emoji support."""

    @staticmethod
    def get_goals(user_id):
        res = db.execute(
            "SELECT id, name, target_amount, current_amount, deadline, icon FROM goals WHERE user_id = ?", (user_id,)
        )
        if res and res.rows:
            return pd.DataFrame(
                res.rows, columns=["id", "Name", "Target", "Current", "Deadline", "Icon"]
            )
        return pd.DataFrame(
            columns=["id", "Name", "Target", "Current", "Deadline", "Icon"]
        )

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
