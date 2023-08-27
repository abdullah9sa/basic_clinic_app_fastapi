# client.py

import asyncio
import socketio

sio_client = socketio.AsyncClient()

@sio_client.event
async def connect():
    print('I\'m connected')

@sio_client.event
async def disconnect():
    print('I\'m disconnected')

@sio_client.event
async def notification(data):
    message = data.get('message')
    print(f'Received a Notification: {message}')

async def main():
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhYmJhcyIsImV4cCI6MTY5MzE2OTQ3NH0.3IXwkWpHmPvJYakaWITW37hl2vTsUc3z3FG88pcWbjE" 
    auth = {'token': token}
    await sio_client.connect(url=f'http://localhost:8000', socketio_path='sockets', auth=auth)
    await asyncio.sleep(60)  # Keep the client connected for 60 seconds
    await sio_client.disconnect()

asyncio.run(main())
