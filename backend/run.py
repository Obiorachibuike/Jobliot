import os, uvicorn
if __name__=="__main__":
    uvicorn.run("app.main:app",host="127.0.0.1",port=int(os.environ.get("CAREERPILOT_PORT","8765")))
