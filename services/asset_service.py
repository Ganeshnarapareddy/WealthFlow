import uuid
import pandas as pd
from database import db

class AssetService:
    @staticmethod
    def get_assets(user_id):
        res = db.execute("SELECT id, name, type, value FROM assets WHERE user_id = ?", (user_id,))
        if res and res.rows:
            return pd.DataFrame(res.rows, columns=['id', 'Name', 'Type', 'Value'])
        return pd.DataFrame(columns=['id', 'Name', 'Type', 'Value'])

    @staticmethod
    def add_asset(name, asset_type, value, user_id):
        aid = str(uuid.uuid4())
        query = "INSERT INTO assets (id, name, type, value, user_id) VALUES (?, ?, ?, ?, ?)"
        db.execute(query, (aid, name, asset_type, value, user_id))

    @staticmethod
    def update_asset(asset_id, name, asset_type, value):
        query = "UPDATE assets SET name = ?, type = ?, value = ? WHERE id = ?"
        db.execute(query, (name, asset_type, value, asset_id))

    @staticmethod
    def delete_asset(asset_id):
        db.execute("DELETE FROM assets WHERE id = ?", (asset_id,))

    @staticmethod
    def get_total_assets_value(user_id):
        res = db.execute("SELECT SUM(value) FROM assets WHERE user_id = ?", (user_id,))
        return float(res.rows[0][0]) if res and res.rows and res.rows[0][0] else 0.0
