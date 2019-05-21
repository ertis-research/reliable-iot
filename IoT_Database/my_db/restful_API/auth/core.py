from passlib.utils import rounds_cost_values

from my_db.db_mongo.model import Token
from passlib.hash import pbkdf2_sha256
from my_db.settings import SECRET_KEY
import datetime
import jwt
import uuid

ALGORITHM = 'HS256'
TYPES = ['USER', 'DEVICE', 'COMPONENT']


def generate(info):
    payload = {
        'iat': int(datetime.datetime.utcnow().timestamp())  # issued at time (timestamp: int)
    }

    if info['type'] == 'USER':  # User tokens expire after 30m
        payload['ex'] = int((datetime.datetime.utcnow()+datetime.timedelta(hours=0.5)).timestamp())  # EXPIRE FOR USERS

    payload.update(info)
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    new_tk = Token()
    new_tk._id = uuid.uuid4().__str__()
    new_tk.token = token.decode('utf-8')
    new_tk.type = info['type']
    new_tk.save()

    return new_tk._id


def validate(token):
    try:
        valid = 0  # we suppose it's not valid

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        tk = Token.objects(token=token)  # works fine

        if tk.count():  # check in the db if it's revoked
            valid = not tk.first().revoked
            if valid and payload['type'] == 'USER':  # if not revoked we check if its USER type and if token expired
                now = int(datetime.datetime.utcnow().timestamp())
                valid = payload['ex'] > now
        return valid
    except:
        return False


def revoke(token):
    tk = Token.objects(token=token, revoked=False)
    if tk.count():
        tk = tk.first()
        tk.revoked = True
        tk.save()


def make_hash(pwd):
    return pbkdf2_sha256.encrypt(pwd, rounds=200000, salt_size=0)
