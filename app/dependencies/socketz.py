import socketio
import jwt
from fastapi.security import OAuth2PasswordBearer
from app.models.user import User
from app.models.user import User, Notification

room_sockets = {}

sio_server = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins=[])

SECRET_KEY = "12345678"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def authenticate(environ, auth):
    print("Authinticating ...")

    jwt_token = auth.get('token')#environ.get("QUERY_STRING", "").replace("token=", "")
    # Verify JWT token and get user_id
    try:
        payload = jwt.decode(jwt_token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
    except jwt.ExpiredSignatureError:
        # raise socketio.exceptions.ConnectionRefusedError("JWT token expired")
        print("JWT token expired")
        return None
    except jwt.DecodeError:
        # raise socketio.exceptions.ConnectionRefusedError("Invalid JWT token")
        print("Invalid JWT token")
        return None

    print("username")
    print(user_id)
    user = await User.get_or_none(username=user_id)

    # Your authentication logic using the user object
    is_authenticated = True  # Replace this with your actual authentication logic

    if not is_authenticated:
        return None
        raise socketio.exceptions.ConnectionRefusedError("Authentication failed")
    
    print("auth seccesfuly")
    return user
    
sio_server.on("connect")(authenticate)

class ConnectionRefusedException(Exception):
    pass

@sio_server.event
async def connect(sid, environ, auth):
    user = await authenticate(environ, auth)
    if user:
        user_id = user.id
    else:
        print("Connection failed: Authentication error")
        raise ConnectionRefusedException("Authentication failed")

    room_sockets[sid] = user_id  # Store the user ID associated with the socket


@sio_server.on("disconnect")
async def on_disconnect(sid):
    room_sid = next((room_sid for room_sid, s in room_sockets.items() if s == sid), None)
    if room_sid:
        del room_sockets[room_sid]

async def emit_notification_to_receiver(notification, receiver_id):
    print("called")
    room_sid = next((sid for sid, user_id in room_sockets.items() if user_id == receiver_id), None)
    if room_sid:
        print(room_sid)
        await sio_server.emit('notification', {'message': notification.message}, room=room_sid)


sio_app = socketio.ASGIApp(socketio_server=sio_server, socketio_path='sockets')
