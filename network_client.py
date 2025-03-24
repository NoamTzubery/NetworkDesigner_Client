import json


async def send_configuration(websocket, configuration):
    await websocket.send(json.dumps(configuration))
    response_str = await websocket.recv()
    response = json.loads(response_str)
    return response
