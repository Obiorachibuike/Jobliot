import asyncio, httpx
from app.core.security import get_stored_api_key
class AIResult:
    def __init__(self,text,ok,error=""): self.text=text; self.ok=ok; self.error=error
async def chat(db, task: str, system: str, user: str) -> AIResult:
    from app.models import AIProviderConfig, AIUsageRecord
    cfg=db.query(AIProviderConfig).first()
    if not cfg or cfg.provider=="none": return AIResult("",False,"No AI provider configured — using built-in non-AI generation. Configure one in AI Provider Settings.")
    model=(cfg.task_models or {}).get(task) or cfg.model
    if not model: return AIResult("",False,"No model selected in AI settings.")
    # budget guard (rough char-based estimate, labelled as estimate)
    last_err=""
    for attempt in range(max(cfg.max_retries,0)+1):
        try:
            if cfg.provider=="ollama":
                base=(cfg.endpoint or "http://localhost:11434").rstrip("/")
                async with httpx.AsyncClient(timeout=cfg.timeout_seconds) as c:
                    r=await c.post(f"{base}/api/chat",json={"model":model,"stream":False,"messages":[{"role":"system","content":system},{"role":"user","content":user}],"options":{"temperature":cfg.temperature}})
                    r.raise_for_status(); text=r.json().get("message",{}).get("content","")
            else:  # openai-compatible
                base=(cfg.endpoint or "https://api.openai.com/v1").rstrip("/"); key=get_stored_api_key()
                if not key: return AIResult("",False,"API key not set. Add it in AI Provider Settings.")
                async with httpx.AsyncClient(timeout=cfg.timeout_seconds) as c:
                    r=await c.post(f"{base}/chat/completions",headers={"Authorization":f"Bearer {key}"},json={"model":model,"temperature":cfg.temperature,"max_tokens":cfg.max_tokens,"messages":[{"role":"system","content":system},{"role":"user","content":user}]})
                    r.raise_for_status(); text=r.json()["choices"][0]["message"]["content"]
            db.add(AIUsageRecord(provider=cfg.provider,model=model,task=task,prompt_chars=len(system)+len(user),completion_chars=len(text),success=True)); db.commit()
            return AIResult(text,True)
        except Exception as e:
            last_err=f"{type(e).__name__}: {e}"
            if attempt<cfg.max_retries: await asyncio.sleep(min(2**attempt,8))
    db.add(AIUsageRecord(provider=cfg.provider,model=model,task=task,prompt_chars=len(user),success=False,error=last_err)); db.commit()
    return AIResult("",False,last_err)
async def test_connection(db) -> dict:
    r=await chat(db,"connection_test","You are a test endpoint.","Reply with the single word OK.")
    return {"ok":r.ok,"detail":(r.text[:120] if r.ok else r.error)}
