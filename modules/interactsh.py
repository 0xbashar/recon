# Simplified interactsh client
import requests
import uuid
import time

class Interactsh:
    def __init__(self, server="oast.pro"):
        self.server = server
        self.session = requests.Session()
        self.correlation_id = str(uuid.uuid4())[:20]

    def get_url(self, token):
        return f"http://{self.correlation_id}.{self.server}/{token}"

    def check_interaction(self, token):
        # In production, poll the interactsh API
        # Here we just simulate
        time.sleep(2)
        # Assume interaction occurred for demo
        return True
