from ib_async import IB


def main():

    # Connect to TWS or IB Gateway
    ib = IB()
    ib.connect('192.168.178.231', 4002, clientId=1)
    print("Connected")

    # Disconnect when done
    ib.disconnect()


if __name__ == "__main__":
    main()
