from fastapi import APIRouter, Depends, HTTPException
from app.models.user import *
from app.serializers.serializers import *
from app.models.user import User
import jwt
from tortoise.transactions import in_transaction
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt.exceptions import DecodeError
from fastapi import Depends, HTTPException, status
from fastapi import Header
from app.dependencies import socketz

router = APIRouter()

SECRET_KEY = "12345678"
ALGORITHM = "HS256"

# OAuth2PasswordBearer for JWT authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Create a role
@router.post("/create-role/", response_model=RoleResponse)
async def create_role(role: RoleCreate):
    return await Role.create(**role.dict())

# Get all available roles
@router.get("/get-roles/")
async def get_roles():
    roles = await Role.all()
    return roles

# Create a patient without associating users
@router.post("/create-patient/", response_model=PatientOut)
async def create_patient(patient: PatientCreate):
    patient_obj = await Patient.create(**patient.dict())
    return patient_obj

def decode_jwt(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except DecodeError as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    


def authenticate_token(authorization: str = Header(default=None)):
    if authorization is None:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    # Assuming the token is in the format "Bearer <token>"
    try:
        _, token = authorization.split()
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token format")

    return token

async def get_current_user(token: str = Depends(authenticate_token)):
    try:
        payload = jwt.decode(token, "12345678", algorithms=["HS256"])
        user_id = payload.get("sub")

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="JWT token expired")
    except jwt.DecodeError:
        raise HTTPException(status_code=401, detail="Invalid JWT token")
    user = await User.get_or_none(username=user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user

@router.post("/transfer-patient/", response_model=PatientOut, tags=["Patients"])
async def transfer_patient(
    transfer_data: PatientTransferIn,
    auth: dict = Depends(get_current_user)  # Pass the token to the dependency
):
    if not auth:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Fetch the patient by ID with related access_users
    patient = await Patient.filter(id=transfer_data.patient_id).prefetch_related('access_users').first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Fetch the receiver user
    receiver = await User.get_or_none(id=transfer_data.receiver_id)
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver user not found")

    # Verify that the sender is authorized to transfer the patient
    if auth.id not in [user.id for user in patient.access_users]:
        raise HTTPException(status_code=403, detail="Unauthorized to transfer patient")

    # Perform the transfer in a transaction
    async with in_transaction():
        patient.access_users.clear()  # Remove existing access users
        await patient.access_users.add(receiver)  # Add receiver as access user

        # Create a PatientTransfer object
        transfer = await PatientTransfer.create(sender=auth, receiver=receiver, patient=patient, some_info=transfer_data.some_info)

    # Create a notification for the new receiver
    notification_message = f"You have been granted access to patient {patient.name}"
    notification = await Notification.create(receiver=receiver, message=notification_message)
    await socketz.emit_notification_to_receiver(notification, receiver.id)

    access_users_ids = [user.id for user in await patient.access_users.all()]

    # Construct the response model
    patient_response = PatientOut(
        id=patient.id,
        name=patient.name,
        medical_info=patient.medical_info,
        access_users=access_users_ids
    )

    return patient_response

## this addes user to patient acces list without authorization, for testing purposes
@router.post("/add-user-to-patient/", response_model=PatientOut)
async def add_user_to_patient(
    transfer_data: PatientTransferIn,
    auth: dict = Depends(get_current_user)  # Pass the token to the dependency
):
    if not auth:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Fetch the patient by ID with related access_users
    patient = await Patient.filter(id=transfer_data.patient_id).prefetch_related('access_users').first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Fetch the user to be added to access_users
    user_to_add = await User.get_or_none(id=transfer_data.receiver_id)
    if not user_to_add:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify that the user has the necessary permissions to add users
    if auth.id not in [user.id for user in patient.access_users]:
        raise HTTPException(status_code=403, detail="Unauthorized to modify patient access")

    print(user_to_add)

    # Add the user to the patient's access_users list
    await patient.access_users.add(user_to_add)

    # Create a notification for the new receiver
    notification_message = f"You have been granted access to patient {patient.name}"
    notification = await Notification.create(receiver=user_to_add, message=notification_message)
    await socketz.emit_notification_to_receiver(notification, user_to_add.id)

    # Extract the IDs of access users for the response
    access_users_ids = [user.id for user in await patient.access_users.all()]

    # Construct the response model
    patient_response = PatientOut(
        id=patient.id,
        name=patient.name,
        medical_info=patient.medical_info,
        access_users=access_users_ids
    )

    return patient_response


## this removes user to patient acces list without authorization, for testing purposes
@router.post("/remove-user-from-patient/", response_model=PatientOut, tags=["Patients"])
async def remove_user_from_patient(
    transfer_data: PatientTransferIn,
    auth: dict = Depends(get_current_user)  # Pass the token to the dependency
):
    if not auth:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Fetch the patient by ID with related access_users
    patient = await Patient.filter(id=transfer_data.patient_id).prefetch_related('access_users').first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Fetch the user to be removed from access_users
    user_to_remove = await User.get_or_none(id=transfer_data.receiver_id)
    if not user_to_remove:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify that the user has the necessary permissions to remove users
    if auth.id not in [user.id for user in patient.access_users]:
        raise HTTPException(status_code=403, detail="Unauthorized to modify patient access")

    # Remove the user from the patient's access_users list
    await patient.access_users.remove(user_to_remove)

    # Create a notification for the removed user
    notification_message = f"Your access to patient {patient.name} has been revoked"
    notification = await Notification.create(receiver=user_to_remove, message=notification_message)
    await socketz.emit_notification_to_receiver(notification, user_to_remove.id)

    # Extract the IDs of access users for the response
    access_users_ids = [user.id for user in await patient.access_users.all()]

    # Construct the response model
    patient_response = PatientOut(
        id=patient.id,
        name=patient.name,
        medical_info=patient.medical_info,
        access_users=access_users_ids
    )

    return patient_response


# Get patient data with authentication
@router.get("/get-patient/{patient_id}/", response_model=PatientOut)
async def get_patient(
    patient_id: int,
    auth: dict = Depends(get_current_user)  # Pass the token to the dependency
):
    if not auth:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    patient = await Patient.filter(id=patient_id).prefetch_related('access_users').first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Check if the authenticated user is in the patient's access list
    if auth.id not in [user.id for user in patient.access_users]:
        raise HTTPException(status_code=403, detail="Unauthorized to access patient info")

    # Construct the response model
    access_users_ids = [user.id for user in patient.access_users]
    patient_out = PatientOut(
        id=patient.id,
        name=patient.name,
        medical_info=patient.medical_info,
        access_users=access_users_ids
    )

    return patient_out
