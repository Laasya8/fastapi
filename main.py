import webhook_receiver
import httpx
from fastapi import FastAPI,BackgroundTasks
from models import WebhookCreate,WebhookResponse,WebhookUpdate,EventCreate
from supabase import create_client
from dotenv import load_dotenv
import os
load_dotenv()

supabase_url=os.getenv("SUPABASE_URL")
supabase_key=os.getenv("SUPABASE_KEY")
supabase=create_client(supabase_url,supabase_key)

app = FastAPI()

#CRUD-CREATE,READ,UPDATE,DELETE
@app.get("/")
def home():
    response=supabase.table("webhooks").select("*").execute()
    return response.data

#create 
@app.post("/webhooks")
def create_webhook(webhook:WebhookCreate):
    response=supabase.table("webhooks").insert({
        "url":webhook.url,
        "event_type":webhook.event_type,
        "is_active":webhook.is_active
    }).execute() 
    return response.data

#read the all id
@app.get("/webhooks")
def get_webhooks():
    response=supabase.table("webhooks").select("*").execute()
    return response.data

#read the specific id
@app.get("/webhooks/{id}")
def get_webhook_by_id(id:int):
    response=supabase.table("webhooks").select("*").eq("id",id).execute()
    return response.data

#update 
@app.put("/webhooks/{id}")
def update_webhook(id:int,webhook:WebhookUpdate):
    response=supabase.table("webhooks").update({
        "url":webhook.url,
        "event_type":webhook.event_type,
        "is_active": webhook.is_active
    }).eq("id",id).execute()
    return response.data

#delete
@app.delete("/webhooks/{id}")
def delete_webhook(id:int):
    response=supabase.table("webhooks").delete().eq("id",id).execute()
    return response.data

def deliver_webhook(webhook, event, delivery_id):
    for attempt in range(1,4):
            try:
                delivery_http_response=httpx.post(
                    webhook["url"],
                    json={
                        "event_type": event.event_type,
                        "payload": event.payload
                    },
                    timeout=5
                )

                if 200<=delivery_http_response.status_code<300:
                    status="success"
                else:
                    status="failed"
                response_code=delivery_http_response.status_code
            except httpx.RequestError:
                status = "failed"
                response_code = None
        
            supabase.table("deliveries").update({
                "status": status,
                "response_code": response_code,
                "attempt_count": attempt
            }).eq("id", delivery_id).execute()

            if status == "success":
                break

@app.post("/events")
def create_event(event:EventCreate,background_tasks:BackgroundTasks):

    event_response=supabase.table("events").insert({
        "event_type":event.event_type,
        "payload":event.payload
    }).execute()

    event_id = event_response.data[0]["id"]

    webhooks=supabase.table("webhooks").select("*").eq("event_type",event.event_type).eq("is_active",True).execute()
    for webhook in webhooks.data:
        delivery_response=supabase.table("deliveries").insert({
            "webhook_id": webhook["id"],
            "event_id": event_id,
            "status": "pending",
            "attempt_count": 0
        }).execute()
        delivery_id=delivery_response.data[0]["id"]

        background_tasks.add_task(
            deliver_webhook,
            webhook,
            event,
            delivery_id
        )
    
    return {
        "event":event_response.data,
        "webhooks":webhooks.data
    }

@app.get("/deliveries")
def get_deliveries():

    response=supabase.table("deliveries").select("*").execute()

    return response.data

@app.get("/events/{event_id}/deliveries")
def get_event_deliveries(event_id: int):

    response=supabase.table("deliveries").select("*").eq("event_id",event_id).execute()

    return response.data