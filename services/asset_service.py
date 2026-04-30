import uuid
import pandas as pd
from database import db

class AssetService:
    @staticmethod
    def get_assets():
        res = db.execute("SELECT id, name, type, value FROM assets")
        if res and res.rows:
            return pd.DataFrame(res.rows, columns=['id', 'Name', 'Type', 'Value'])
        return pd.DataFrame(columns=['id', 'Name', 'Type', 'Value'])

    @staticmethod
    def add_asset(name, asset_type, value):
        aid = str(uuid.uuid4())
        user_id = 'default_user'
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
    def get_total_assets_value():
        res = db.execute("SELECT SUM(value) FROM assets")
        return float(res.rows[0][0]) if res and res.rows and res.rows[0][0] else 0.0
