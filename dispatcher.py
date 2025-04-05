import asyncio
import json


class WebSocketDispatcher:
    def __init__(self, websocket):
        self.websocket = websocket
        self.queue = asyncio.Queue()
        # Start the central receiver task.
        self._receiver_task = asyncio.create_task(self._receiver())

    async def _receiver(self):
        try:
            while True:
                message = await self.websocket.recv()
                try:
                    data = json.loads(message)
                except Exception as e:
                    print("Error decoding JSON:", e)
                    continue
                await self.queue.put(data)
        except asyncio.CancelledError:
            # Gracefully exit on cancellation.
            print("Receiver task cancelled.")
        except Exception as e:
            print("Dispatcher receiver encountered exception:", e)
        finally:
            print("Receiver task exiting.")

    async def send_and_wait(self, request, timeout=5):
        try:
            # Send the request.
            await self.websocket.send(json.dumps(request))
            # Wait for the next response from the queue.
            response = await asyncio.wait_for(self.queue.get(), timeout=timeout)
            return response
        except Exception as e:
            print("send_and_wait error:", e)
            raise

    async def send(self, request):
        try:
            await self.websocket.send(json.dumps(request))
        except Exception as e:
            print("Send error:", e)
            raise

    async def close(self):
        if self._receiver_task:
            self._receiver_task.cancel()
            try:
                await self._receiver_task
            except Exception as e:
                print("Receiver task cancelled with exception:", e)
