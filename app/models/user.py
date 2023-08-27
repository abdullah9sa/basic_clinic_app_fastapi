from tortoise import Model, fields
import datetime

class Role(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=50)

class User(Model):
    id = fields.IntField(pk=True, index=True)
    username = fields.CharField(max_length=20, null=False, unique=True)
    password = fields.CharField(max_length=100, null=False)
    join_date = fields.DatetimeField(default=datetime.datetime.utcnow)
    role = fields.ForeignKeyField('models.Role', related_name='users')

class Patient(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=200)
    access_users = fields.ManyToManyField('models.User', related_name='patients')
    medical_info = fields.TextField()

class Notification(Model):
    id = fields.IntField(pk=True)
    receiver = fields.ForeignKeyField('models.User', related_name='notifications')
    message = fields.TextField()
    is_read = fields.BooleanField(default=False)
    creation_date = fields.DatetimeField(auto_now_add=True)

class PatientTransfer(Model):
    id = fields.IntField(pk=True)
    sender = fields.ForeignKeyField('models.User', related_name='sent_transfers')
    receiver = fields.ForeignKeyField('models.User', related_name='received_transfers')
    patient = fields.ForeignKeyField('models.Patient', related_name='transfers')
    some_info = fields.TextField()
    transfer_date = fields.DatetimeField(auto_now_add=True)
