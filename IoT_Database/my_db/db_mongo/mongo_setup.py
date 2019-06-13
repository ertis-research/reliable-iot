import mongoengine


def global_init():
    return mongoengine.connect(
        "IoT",
        host=['mongo_db:27017']
    )
