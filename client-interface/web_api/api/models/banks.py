from typing import List
from pydantic import BaseModel


class BankPedalboard(BaseModel):
    title: str
    bundlepath: str
    broken: bool
    hasScreenshot: bool


class Bank(BaseModel):
    title: str
    pedalboards: List[BankPedalboard]


class BankSaveRequest(BaseModel):
    banks: List[Bank]
