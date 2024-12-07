from pydantic import BaseModel
from typing import List

class WebUiConfiguration(BaseModel):
    title: str
    logo: str
    bot_name: str
    suggested_prompt: List[str]

class SdkConfiguration(BaseModel):
    bot_name: str
    