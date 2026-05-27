from pydantic import BaseModel
from typing import List, Optional


class VehiclePlate(BaseModel):
    id: int
    plate: str


class VehicleResponse(BaseModel):
    vehicles: List[VehiclePlate]


class MethaneData(BaseModel):
    id: int
    location: List[float]
    methane_percentage: float
    last_update: float


class MethaneResponse(BaseModel):
    methane: List[MethaneData]


class ObjectData(BaseModel):
    id: int
    type: str
    position: List[float]


class WebSocketData(BaseModel):
    objects: List[ObjectData]