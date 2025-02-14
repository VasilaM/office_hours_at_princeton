import requests
import json
import base64
import os

class Configs:
    def __init__(self, base_url):
        self.CONSUMER_KEY = os.environ['PRINCETON_API_KEY']
        self.CONSUMER_SECRET = os.environ['PRINCETON_API_SECRET']
        # for student app: "https://api.princeton.edu:443/student-app/1.0.3"
        self.BASE_URL = base_url
        self.COURSE_COURSES="/courses/courses"
        self.COURSE_TERMS="/courses/terms"
        self.DINING_LOCATIONS="/dining/locations"
        self.DINING_EVENTS="/dining/events"
        self.DINING_MENU="/dining/menu"
        self.PLACES_OPEN="/places/open"
        self.EVENTS_EVENTS="/events/events"
        self.USERS="/users"
        self.REFRESH_TOKEN_URL="https://api.princeton.edu:443/token"
        self._refreshToken(grant_type="client_credentials")

    def _refreshToken(self, **kwargs):
        req = requests.post(
            self.REFRESH_TOKEN_URL, 
            data=kwargs, 
            headers={
                "Authorization": "Basic " + base64.b64encode(bytes(self.CONSUMER_KEY + ":" + self.CONSUMER_SECRET, "utf-8")).decode("utf-8")
            },
        )
        text = req.text
        response = json.loads(text)
        self.ACCESS_TOKEN = response["access_token"]