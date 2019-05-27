import mongoengine


def global_init():
    # return mongoengine.connect(
    #     "IoT",
    #     host=['mongo_db:27017']
    # )

    return mongoengine.connect(
        "IoT",
        host=['127.0.0.1:27017']
    )
