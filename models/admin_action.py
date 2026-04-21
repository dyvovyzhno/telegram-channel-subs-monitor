# models/admin_action.py

import hashlib


class AdminAction:
    def __init__(
        self,
        action: str,
        date: str,
        user_id: int,
        user_username: str,
        user_firstname: str,
        user_lastname: str,
        total_channel_members: int,
        total_joined: int,
        total_left: int,
        user_phone: str,
    ):
        self.action = action
        self.date = date
        self.user_id = user_id
        self.user_username = user_username
        self.user_firstname = user_firstname
        self.user_lastname = user_lastname
        self.total_channel_members = total_channel_members
        self.total_joined = total_joined
        self.total_left = total_left
        self.user_phone = user_phone
        self.hash = self.generate_hash()

    def generate_hash(self) -> str:
        """Generate a hash based on user_id and date."""
        # Combine user_id and date into a string, then hash
        combined = f"{self.user_id}|{self.date}"
        return hashlib.sha256(combined.encode()).hexdigest()

    def to_dict(self) -> dict:
        """Converts the object to a dictionary, suitable for Firebase storage."""
        return {
            "hash": self.hash,
            "action": self.action,
            "date": self.date,
            "user_id": self.user_id,
            "user_username": self.user_username,
            "user_firstname": self.user_firstname,
            "user_lastname": self.user_lastname,
            "user_phone": self.user_phone,
            "total_channel_members": self.total_channel_members,
            "total_joined": self.total_joined,
            "total_left": self.total_left,
        }
