from __future__ import annotations
import json
import random
import time
from dataclasses import dataclass
from typing import Any, Protocol
import httpx

@dataclass
class Completion:
    content: str
    model: str
    prompt_tokens: int=0
    completion_tokens: int=0
    latency_ms: int=0

class ClientProtocol(Protocol):
    def list_models(self)->list[str]: ...
    def complete(self,messages:list[dict[str,str]],model:str,temperature:float=.2,max_tokens:int=400,json_mode:bool=False)->Completion: ...

class GroqClient:
    def __init__(self,api_key:str,base_url:str,timeout:float=20.0,http:Any|None=None):
        self.api_key=api_key;self.base_url=base_url.rstrip("/");self.timeout=timeout
        self.http=http or httpx.Client(timeout=timeout)
    def _headers(self):return {"Authorization":f"Bearer {self.api_key}","Content-Type":"application/json"}
    def list_models(self)->list[str]:
        response=self.http.get(f"{self.base_url}/models",headers=self._headers(),timeout=self.timeout)
        response.raise_for_status()
        return [str(x.get("id")) for x in response.json().get("data",[]) if x.get("id")]
    def complete(self,messages:list[dict[str,str]],model:str,temperature:float=.2,max_tokens:int=400,json_mode:bool=False)->Completion:
        payload={"model":model,"messages":messages,"temperature":temperature,"max_tokens":max_tokens}
        if json_mode:payload["response_format"]={"type":"json_object"}
        started=time.monotonic();last_error=None
        for attempt in range(3):
            try:
                response=self.http.post(f"{self.base_url}/chat/completions",headers=self._headers(),json=payload,timeout=self.timeout)
                if response.status_code==429 or response.status_code>=500:
                    if attempt<2:
                        retry=response.headers.get("Retry-After")
                        delay=min(8.0,float(retry)) if retry and retry.replace('.','',1).isdigit() else min(4.0,.5*(2**attempt)+random.random()*.15)
                        time.sleep(delay);continue
                response.raise_for_status();body=response.json();choice=body["choices"][0]["message"].get("content","")
                usage=body.get("usage") or {}
                return Completion(str(choice),str(body.get("model",model)),int(usage.get("prompt_tokens",0)),int(usage.get("completion_tokens",0)),int((time.monotonic()-started)*1000))
            except (httpx.TimeoutException,httpx.TransportError,httpx.HTTPStatusError,ValueError,KeyError) as exc:
                last_error=exc
                if isinstance(exc,httpx.HTTPStatusError) and exc.response.status_code not in {429,500,502,503,504}:raise
                if attempt<2:time.sleep(min(4.0,.5*(2**attempt)+random.random()*.15))
        raise RuntimeError(f"Groq request failed after retries: {type(last_error).__name__ if last_error else 'unknown error'}")

class FakeClient:
    """Deterministic no-network test double."""
    def __init__(self,responses:list[str]|None=None,models:list[str]|None=None):
        self.responses=list(responses or ['{"ok":true}']);self.models=models or ["fake-chat-model"];self.calls=[]
    def list_models(self):return self.models
    def complete(self,messages,model,temperature=.2,max_tokens=400,json_mode=False):
        self.calls.append({"messages":messages,"model":model,"temperature":temperature,"max_tokens":max_tokens,"json_mode":json_mode})
        value=self.responses.pop(0) if len(self.responses)>1 else self.responses[0]
        return Completion(value,model,12,8,3)
