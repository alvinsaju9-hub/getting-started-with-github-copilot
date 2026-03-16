import os
import base64
from typing import List, Optional
from os.path import dirname, abspath, join
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

current_dir = dirname(abspath(__file__))
static_path = join(current_dir, "static")

app = FastAPI()
app.mount("/ui", StaticFiles(directory=static_path), name="ui")


class Body(BaseModel):
    length: Optional[int] = 20


class Activity(BaseModel):
    id: int
    name: str
    description: str
    category: str
    active: bool = True


class ActivityCreate(BaseModel):
    name: str
    description: str
    category: str
    active: bool = True


activities_data_path = join(current_dir, "activities.json")


def _default_activities() -> List[Activity]:
    return [
        Activity(id=1, name="Coding Club", description="Weekly coding workshops", category="STEM", active=True),
        Activity(id=2, name="Drama Society", description="Theater production and rehearsal", category="Arts", active=True),
        Activity(id=3, name="AI Animation Club", description="Create animated stories with AI tools", category="Technology & Arts", active=True),
    ]


def load_activities() -> List[Activity]:
    if os.path.exists(activities_data_path):
        try:
            with open(activities_data_path, "r", encoding="utf-8") as f:
                raw = f.read().strip()
                if raw:
                    from json import loads
                    data = loads(raw)
                    return [Activity(**item) for item in data]
        except Exception:
            pass
    return _default_activities()


def save_activities():
    from json import dumps
    with open(activities_data_path, "w", encoding="utf-8") as f:
        f.write(dumps([activity.dict() for activity in activities], indent=2))


activities: List[Activity] = load_activities()


def _get_next_id() -> int:
    if not activities:
        return 1
    return max(activity.id for activity in activities) + 1


@app.get('/')
def root():
    html_path = join(static_path, "index.html")
    return FileResponse(html_path)


@app.post('/generate')
def generate(body: Body):
    """
    Generate a pseudo-random token ID of twenty characters by default. Example POST request body:

    {
        "length": 20
    }
    """
    string = base64.b64encode(os.urandom(64))[:body.length].decode('utf-8')
    return {'token': string}


@app.get('/activities', response_model=List[Activity])
def list_activities():
    return activities


@app.post('/activities', response_model=Activity, status_code=201)
def add_activity(activity_in: ActivityCreate):
    new_activity = Activity(id=_get_next_id(), **activity_in.dict())
    activities.append(new_activity)
    save_activities()
    return new_activity


@app.get('/activities/{activity_id}', response_model=Activity)
def get_activity(activity_id: int):
    for activity in activities:
        if activity.id == activity_id:
            return activity
    raise HTTPException(status_code=404, detail='Activity not found')