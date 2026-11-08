from sqlalchemy import Column, String, Float, Integer, Boolean, Text
from app.database import Base

class GTFSStop(Base):
    __tablename__ = "gtfs_stops"

    stop_id = Column(String(100), primary_key=True, index=True)
    city = Column(String(50), nullable=False, index=True, default="delhi")
    stop_name = Column(String(200), nullable=False, index=True)
    stop_desc = Column(Text, nullable=True)
    stop_lat = Column(Float, nullable=False)
    stop_lon = Column(Float, nullable=False)
    zone_id = Column(String(50), nullable=True)
    wheelchair_boarding = Column(Integer, default=0)

class GTFSRoute(Base):
    __tablename__ = "gtfs_routes"

    route_id = Column(String(100), primary_key=True, index=True)
    city = Column(String(50), nullable=False, index=True, default="delhi")
    route_short_name = Column(String(50), nullable=False, index=True) # e.g. "534", "502"
    route_long_name = Column(String(255), nullable=False)
    route_type = Column(Integer, default=3) # 3 = Bus
    bus_type = Column(String(50), default="Ordinary") # "AC_LowFloor", "Ordinary", "Electric"
    fare_tier = Column(String(50), default="standard")
