from snapex import Client

def main():
    # Example usage
    with Client() as client:
        # Simple GET request
        response = client.get('https://httpbin.org/get')
        print(f"Status: {response.status_code}")
        print(f"Headers: {response.headers}")
        print(f"Body: {response.text[:100]}...")

        # POST request with JSON
        response = client.post('https://httpbin.org/post', json={'key': 'value'})
        print(f"JSON Response: {response.json()}")

        # Stream download with progress
        print("Downloading file...")
        for chunk in client.stream('GET', 'https://httpbin.org/bytes/1024', 
                                on_progress=lambda c, t: print(f"\rDownloaded: {c}/{t} bytes", end='')):
            pass
        print("\nDownload complete!")

        # WebSocket example
        async def websocket_example():
            async with client.websocket('wss://echo.websocket.org') as ws:
                await ws.send("Hello, WebSocket!")
                response = await ws.recv()
                print(f"WebSocket response: {response}")

        import asyncio
        asyncio.run(websocket_example())

if __name__ == '__main__':
    main()