# ./app/models.py

from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.ext.declarative import declarative_base
import datetime

# Define the base class
Base = declarative_base()

# Define the Timeseries model
class Energy_consumption_timeseries(Base):
    __tablename__ = 'energy_consumption_timeseries'

    datetime_id = Column(DateTime, primary_key=True, default=datetime.datetime)
    month = Column(Float, nullable=False)
    day = Column(Integer, nullable=False)
    hour = Column(Integer, nullable=False)
    # minute = Column(Integer, nullable=False)
    # electric_demand = Column(Float, nullable=False)
    # temp_value = Column(Float, nullable=False)
    # dewpoint_value = Column(Float, nullable=False)
    # humidity_value = Column(Float, nullable=False)
    location_id = Column(String)