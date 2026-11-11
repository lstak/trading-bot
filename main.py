import os

from dotenv import load_dotenv
from ib_async import IB

load_dotenv()


def main():

    # Connect to IB Gateway
    ib = IB()

    HOST = os.getenv('IBG_HOST', '127.0.0.1')
    PORT = int(os.getenv('IBG_PORT', '4002'))
    CLIENT_ID = int(os.getenv('IBG_CLIENT_UD', '1'))

    ib.connect(
        host=HOST,
        port=PORT,
        clientId=CLIENT_ID,
    )
    print("Connected")

    # Disconnect when done
    ib.disconnect()


if __name__ == "__main__":
    main()
