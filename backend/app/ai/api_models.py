from pydantic import BaseModel,Field

class AIRequest(BaseModel):player:str=Field(min_length=1,max_length=80)
class GenerateQuestionsIn(AIRequest):topic:str=Field(min_length=2,max_length=120);difficulty:str="intermediate";count:int=Field(default=3,ge=1,le=5)
class GradeIn(AIRequest):question_id:str=Field(min_length=1,max_length=120);answer:str=Field(max_length=1200);response_time_ms:int=Field(default=10000,ge=0,le=600000);hint_count:int=Field(default=0,ge=0,le=3)
class HintIn(AIRequest):question_id:str=Field(min_length=1,max_length=120);step:int=Field(default=1,ge=1,le=3)
class MistakeIn(AIRequest):question_id:str=Field(min_length=1,max_length=120);answer:str=Field(max_length=1200)
class SandboxIn(AIRequest):text:str=Field(min_length=1,max_length=2000);topic:str="";other_text:str=Field(default="",max_length=2000)
class ChatTurn(BaseModel):role:str;content:str=Field(max_length=2000)
class AIChatIn(AIRequest):message:str=Field(min_length=1,max_length=1200);history:list[ChatTurn]=Field(default_factory=list,max_length=12)
class PracticeSetIn(AIRequest):topic:str|None=None
class TeachBackIn(AIRequest):topic:str=Field(min_length=2,max_length=120);explanation:str|None=Field(default=None,max_length=2000)
class ErrorHuntIn(AIRequest):sentence:str=Field(min_length=4,max_length=500);task_id:str|None=None;selected_indices:list[int]=Field(default_factory=list,max_length=30)
class MicroLessonIn(AIRequest):topic:str|None=None
class AIFeedbackIn(AIRequest):interaction_id:int;thumbs:int=Field(ge=-1,le=1)
class AIConsentIn(AIRequest):enabled:bool
