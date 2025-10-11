import datetime

class User:
    def __init__(self, username:str, email:str, password:str, 
                 id:str | None = None, created_at:datetime.date | None=None):
        self.id = id
        self.username = username
        self.email = email
        self.password = password
        self.created_at = created_at

class Profile:
    def __init__(self, display_name:str, avatar_url:str, 
                 id:str | None = None, created_at:datetime.date | None=None):
        self.id = id
        self.display_name = display_name
        self.avatar_url = avatar_url
        self.created_at = created_at