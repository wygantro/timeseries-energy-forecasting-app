from initialize import Base
from sqlalchemy import Column, DateTime, Numeric, String

class Electric_demand_records(Base):
    __tablename__ = 'electric_demand_records'
    
    time_stamp = Column(DateTime(), primary_key=True)
    electric_demand = Column(Numeric(15,6))
    #temp_value = Column(Numeric(15,6))
    price = Column(Numeric(15,6))
    location_id = Column(String(15,6))