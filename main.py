from mongoengine import connect
from classes import *
import json
import os
import asyncio
from PIL import Image
from io import BytesIO
from moviepy.editor import VideoFileClip
import numpy as np


from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse, StreamingResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
import paho.mqtt.client as mqtt

app = FastAPI()
connect(db="DEE", host="localhost", port=27017)
client = mqtt.Client(client_id="fastApi", transport='websockets')
is_connected = False

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {str(rc)}")
    client.subscribe("autopilotService/WebApp/telemetryInfo", 2)
    # client.subscribe("+/fastApi/#", 2)


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    global is_connected
    # print(f"{msg.topic} {str(msg.payload)}")
    if msg.topic == "autopilotService/WebApp/telemetryInfo":
        is_connected = True


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder(
            ErrorResponse(
                success=False,
                message="Validation error",
                errors=exc.errors(),
            )
        ),
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(
            ErrorResponse(success=False, message=exc.detail)
        ),
    )

# MQTT Callbacks
client.on_connect = on_connect
client.on_message = on_message

@app.get("/connect")
async def connect_to_broker():
    global is_connected
    try:
        client.connect("localhost", 8000, 10)
        client.loop_start()
        client.publish("WebApp/autopilotService/connect")
        await asyncio.sleep(2)
        if not is_connected:
            raise HTTPException(status_code=503, detail="Connection failed. No telemetryInfo message received.")
        return {"message": "Successfully connected to the broker."}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/disconnect")
async def disconnect_from_broker():
    global is_connected
    try:
        client.publish("WebApp/autopilotService/disconnect")
        client.loop_stop()
        client.disconnect()
        is_connected = False
        return {"message": "Successfully disconnected from the broker."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/connection_status")
async def get_connection_status():
    global is_connected
    return {"is_connected": is_connected}

@app.post("/executeFlightPlan")
async def execute_flight_plan(plan: List[WaypointMQTT]):
    # Convert the FlightPlan to a JSON string
    plan_json = json.dumps(jsonable_encoder(plan))

    # Publish the plan to the MQTT broker
    client.publish("WebApp/autopilotService/executeFlightPlan", plan_json)
    return {"message": "Flight plan published"}
# End MQTT Callbacks

@app.get("/")
def home():
    return RedirectResponse(url="/docs")


@app.get("/get_all_flights")
def get_all_flights():
    flights = Flights.objects()
    flights_data = []

    for flight in flights:
        flight_dict = json.loads(flight.to_json())

        # Populate related documents
        flight_dict["FlightPlan"] = json.loads(flight.FlightPlan.to_json())

        # Pictures
        pictures = []
        for pic_ref in flight.Pictures:
            pic = Picture.objects.get(id=pic_ref.id)
            pictures.append(json.loads(pic.to_json()))
        flight_dict["Pictures"] = pictures

        # Videos
        videos = []
        for vid_ref in flight.Videos:
            vid = Video.objects.get(id=vid_ref.id)
            videos.append(json.loads(vid.to_json()))
        flight_dict["Videos"] = videos

        flights_data.append(flight_dict)

    return flights_data


@app.post("/add_waypoints", response_model=SuccessResponse, responses={422: {"model": ErrorResponse}})
def add_waypoints(data: WaypointData):
    try:
        waypoints = data.waypoints
        pic_interval = data.PicInterval
        vid_interval = data.VidInterval

        num_waypoints = len(waypoints)
        num_pics = 0
        num_vids = 0
        flight_waypoints = []
        pics_waypoints = []
        vid_waypoints = []
        for w in waypoints:
            waypoint = Waypoint(lat=w.lat, lon=w.lon, height=w.height)
            flight_waypoints.append(waypoint)
            if w.takePic:
                pics_waypoints.append(waypoint)
                num_pics += 1
            if w.videoStart or w.videoStop:
                if w.videoStart:
                    num_vids += 1
                    waypoint_vid = VideoPlan(mode="moving", latStart=w.lat, lonStart=w.lon)
                if w.videoStop:
                    waypoint_vid.latEnd = w.lat
                    waypoint_vid.lonEnd = w.lon
                    vid_waypoints.append(waypoint_vid)
            if w.staticVideo:
                num_vids += 1
                static_vid = VideoPlan(mode="static", lat=w.lat, lon=w.lon, length=vid_interval)
                vid_waypoints.append(static_vid)

        new_flight_plan = FlightPlan(NumWaypoints=num_waypoints,
                                     FlightWaypoints=flight_waypoints,
                                     NumPics=num_pics,
                                     PicsWaypoints=pics_waypoints,
                                     NumVids=num_vids,
                                     VidWaypoints=vid_waypoints,
                                     PicInterval=pic_interval)
        new_flight_plan.save()
        return {"success": True, "message": "Waypoints Saved"}

    except Exception as e:
        raise HTTPException(status_code=400, detail={str(e)})


@app.get("/get_all_flightPlans")
def get_all_flightPlans():
    waypoints = json.loads(FlightPlan.objects().to_json())
    return {"Waypoints": waypoints}


# Serve media files
app.mount("/media", StaticFiles(directory="media"), name="media")


@app.get("/media/pictures/{file_name}")
async def get_picture(file_name: str):
    return FileResponse(os.path.join("media", "pictures", file_name))


@app.get("/media/videos/{file_name}")
async def get_video(file_name: str):
    return FileResponse(os.path.join("media", "videos", file_name))



@app.get("/thumbnail/{file_name}")
async def get_video_thumbnail(file_name: str):
    # Load the video
    video = VideoFileClip(f"media/videos/{file_name}")

    thumbnail = video.get_frame(0)
    img = Image.fromarray(np.uint8(thumbnail))

    image_io = BytesIO()
    img.save(image_io, format='JPEG')
    image_io.seek(0)

    return StreamingResponse(image_io, media_type="image/jpeg")




