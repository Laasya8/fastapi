from fastapi import FastAPI
app=FastAPI()

@app.post("/webhook")
def recieve_webhook(data:dict):
    print("webhook received")
    print(data)

    return{"message":"Webhook received successfully"}