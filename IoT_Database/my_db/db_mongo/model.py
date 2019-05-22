import mongoengine


class Resource(mongoengine.Document):
    _id = mongoengine.StringField(required=True, primary_key=True)
    # it's a LWM2M standard code to identify a resource, for example 3303 is temperature
    type = mongoengine.IntField(required=True)
    status = mongoengine.BooleanField(default=True)
    # '3303/0', '3303/1' there can be many providers of one resource (provider 0, provider 1)
    accessing = mongoengine.StringField(required=True)


class Endpoint(mongoengine.Document):
    _id = mongoengine.StringField(required=True, primary_key=True)
    name = mongoengine.StringField(required=True)
    leshan_id = mongoengine.StringField(unique=True)  # Mqtt wont have this, so, not required
    available = mongoengine.BooleanField(default=True)
    address = mongoengine.StringField(required=True)
    resources = mongoengine.ListField(mongoengine.ReferenceField(Resource), default=[])
    events = mongoengine.ListField(default=[])  # this will be a list of events that happen


class Token(mongoengine.Document):
    _id = mongoengine.StringField(required=True, primary_key=True)
    token = mongoengine.StringField(required=True)
    type = mongoengine.StringField(required=True, choices=['USER', 'DEVICE', 'COMPONENT'])
    revoked = mongoengine.BooleanField(default=False)


class IotConnector(mongoengine.Document):
    _id = mongoengine.StringField(required=True, primary_key=True)
    ip = mongoengine.StringField(required=True)
    port = mongoengine.IntField(required=True)
    token = mongoengine.ReferenceField(Token, required=True)
    mac = mongoengine.StringField(required=True)
    type = mongoengine.StringField(required=True)
    endpoints = mongoengine.ListField(mongoengine.ReferenceField(Endpoint), default=[])


class Shadow(mongoengine.Document):
    _id = mongoengine.StringField(required=True, primary_key=True)
    tokens = mongoengine.ListField(mongoengine.ReferenceField(Token), default=[])
    devices = mongoengine.ListField(mongoengine.ReferenceField(IotConnector), default=[])
    name = mongoengine.StringField()
    description = mongoengine.StringField()


class UserData(mongoengine.Document):
    _id = mongoengine.StringField(required=True, primary_key=True)
    username = mongoengine.EmailField(required=True)
    password = mongoengine.StringField(required=True)
    token = mongoengine.ReferenceField(Token, required=True)
    shadow = mongoengine.ListField(mongoengine.ReferenceField(Shadow), default=[])


class Application(mongoengine.Document):
    _id = mongoengine.StringField(required=True, primary_key=True)
    name = mongoengine.StringField(required=True, unique=True)
    interests = mongoengine.ListField(default=[])


# this table is a M-M relationship betweet Applications and Resources
class ResourceUse(mongoengine.Document):
    _id = mongoengine.StringField(required=True, primary_key=True)
    # reverse_delete_rule=mongoengine.CASCADE means that if the Application/Resource referenced is deleted, the EndpointUse too
    application = mongoengine.ReferenceField(Application, reverse_delete_rule=mongoengine.CASCADE, required=True)
    shadow = mongoengine.ReferenceField(Shadow, reverse_delete_rule=mongoengine.CASCADE, required=True)
    iot_connector = mongoengine.ReferenceField(IotConnector, reverse_delete_rule=mongoengine.CASCADE, required=True)
    endpoint = mongoengine.ReferenceField(Endpoint, reverse_delete_rule=mongoengine.CASCADE, required=True)
    resource = mongoengine.ReferenceField(Resource, reverse_delete_rule=mongoengine.CASCADE, required=True)
    kafka_topic = mongoengine.StringField(required=True)


# This collection stores a Type of IOT DEVICE and an associated docker command to deploy it
class DeviceTypeDockerCommand(mongoengine.Document):
    _id = mongoengine.StringField(required=True, primary_key=True)
    type = mongoengine.StringField(required=True)
    image = mongoengine.StringField(required=True)
