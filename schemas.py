from pydantic import BaseModel, validator
from datetime import date, datetime

class UserCreate(BaseModel):
    username: str
    password: str
    role:     str

class LeaveRequest(BaseModel):
    employee_name: str
    leave_type:    str
    start_date:    date
    end_date:      date
    reason:        str

    @validator("end_date")
    def validate_dates(cls, v, values):
        if "start_date" in values and v < values["start_date"]:
            raise ValueError("End date must be >= start date")
        return v

class LeaveResponse(BaseModel):
    id:            int
    employee_name: str
    leave_type:    str
    start_date:    date
    end_date:      date
    reason:        str
    status:        str
    created_at:    datetime
    updated_at:    datetime

    class Config:
        from_attributes = True