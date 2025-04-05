import json


async def send_configuration(dispatcher, configuration):
    response = await dispatcher.send_and_wait(configuration)
    return response
