from __future__ import annotations
import json
from typing import Literal
from pydantic import BaseModel, Field, ValidationError, field_validator

class Citation(BaseModel):title:str;url:str
class QuestionOut(BaseModel):
    type:Literal["multiple_choice","fill_blank","short_answer","tag_sentence"]
    question:str=Field(min_length=5,max_length=500)
    options:list[str]=Field(default_factory=list)
    answer:str=Field(min_length=1,max_length=250)
    explanation:str=Field(min_length=3,max_length=700)
    source_lecture:Citation
    difficulty:Literal["introductory","intermediate","advanced"]
    def check_options(self):
        if self.type=="multiple_choice" and (len(self.options)<2 or self.answer not in self.options):raise ValueError("MCQ answer must be one of its options")
class QuestionListOut(BaseModel):questions:list[QuestionOut]=Field(min_length=1,max_length=5)
class GradeOut(BaseModel):score:float=Field(ge=0,le=1);verdict:Literal["correct","partially_correct","incorrect"];what_was_right:str;what_was_missing:str;misconception:str;hint:str
class HintOut(BaseModel):hint:str=Field(min_length=1,max_length=400)
class MistakeOut(BaseModel):explanation:str=Field(max_length=900);rule:str;hint:str;source_lecture:Citation
class ChatOut(BaseModel):answer:str=Field(min_length=1,max_length=3000);citations:list[Citation]=Field(min_length=1,max_length=3)
class MicroLessonOut(BaseModel):title:str;objective:str;text:str=Field(min_length=100,max_length=1800);practice:list[str]=Field(min_length=3,max_length=3);source_lecture:Citation
class SandboxOut(BaseModel):explanation:str=Field(max_length=1000);interesting_parts:list[str]=Field(max_length=4);possible_errors:list[str]=Field(max_length=4);experiments:list[str]=Field(min_length=2,max_length=2)
class TeachBackOut(BaseModel):follow_up:str=Field(max_length=500);accuracy:float=Field(ge=0,le=1);completeness:float=Field(ge=0,le=1);clarity:float=Field(ge=0,le=1);feedback:str=Field(max_length=800);bonus_xp:int=Field(ge=0,le=20)
class ErrorExplainOut(BaseModel):explanation:str=Field(max_length=700);hint:str=Field(max_length=300)

def parse_json(text:str,schema:type[BaseModel]):
    value=json.loads(text)
    result=schema.model_validate(value)
    if isinstance(result,QuestionOut):result.check_options()
    if isinstance(result,QuestionListOut):
        for question in result.questions:question.check_options()
    return result
