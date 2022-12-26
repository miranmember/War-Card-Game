"""
war card game client and server
"""
import asyncio
from collections import namedtuple
from enum import Enum
import logging
import random
import sys


"""
Namedtuples work like classes, but are much more lightweight so they end
up being faster. It would be a good idea to keep objects in each of these
for each game which contain the game's state, for instance things like the
socket, the cards given, the cards still available, etc.
"""
Game = namedtuple("Game", ["p1", "p2"])

class Command(Enum):
    """
    The byte values sent as the first byte of any message in the war protocol.
    """
    WANTGAME = 0
    GAMESTART = 1
    PLAYCARD = 2
    PLAYRESULT = 3


class Result(Enum):
    """
    The byte values sent as the payload byte of a PLAYRESULT message.
    """
    WIN = 0
    DRAW = 1
    LOSE = 2

def readexactly(sock, numbytes):
    returnV = b''
    while len(returnV) < numbytes:
        returnV += sock.recv(numbytes - len(returnV))
        if len(returnV) == 0:
            print("THERE IS AN ERROR READING THE CLIENT")
            sock.close()
            return
    return returnV

def kill_game(game):
    game[0].close()
    game[1].close()

def compare_cards(card1, card2):
    if (card1 % 13)  < (card2 % 13):
        return Result.LOSE.value
    elif (card1 % 13) > (card2 % 13):
        return Result.WIN.value
    else:
        return Result.DRAW.value

def deal_cards():
    hands = [index for index in range(52)]
    random.shuffle(hands)
    returnHand1 = hands[:26]
    returnHand2 = hands[26:]
    return returnHand1,returnHand2

clients = list()

async def game(client1, client2):
    client1Cards , client2Cards = deal_cards()
    usedCards1 = [False] * 55
    usedCards2 = [False] * 55
    try:
        client1Data = await client1[0].readexactly(2)
        client2Data = await client2[0].readexactly(2)
        if (client1Data[0] != 0) or (client2Data[0] != 0):
            print("USER DID NOT ENTER 0 TO START THE GAME")
            kill_game((client1[1],client2[1]))
            return
        client1[1].write(bytes([Command.GAMESTART.value]+client1Cards))
        client2[1].write(bytes([Command.GAMESTART.value]+client2Cards))
        for i in range(26):
            client1Data = await client1[0].readexactly(2)
            client2Data = await client2[0].readexactly(2)
            if (client1Data[0] != 2) and (client2Data != 2):
                print("USER DID NOT ENTER 2 TO PLAY CARD")
                kill_game((client1[1],client2[2]))
                return
            elif not(client1Data[1] in client1Cards) or not(client2Data[1] in client2Cards):
                print("USER ENTERED CARD NOT IN THEIR HAND")
                kill_game((client1[1],client2[1]))
                return
            elif (usedCards1[client1Data[1]] or usedCards2[client2Data[1]]):
                print("USER ENTERED CARD THAT WAS ALREADY USED")
                kill_game((client1[1],client2[1]))
                return
            else:
                usedCards1[client1Data[1]] = True
                usedCards2[client2Data[1]] = True
            client1[1].write(bytes([Command.PLAYRESULT.value, compare_cards(client1Data[1],client2Data[1])]))
            client2[1].write(bytes([Command.PLAYRESULT.value, compare_cards(client2Data[1],client1Data[1])]))
        kill_game((client1[1], client2[1]))
    except ConnectionResetError:
        logging.error("ConnectionResetError")
        return 0
    except asyncio.streams.IncompleteReadError:
        logging.error("asyncio.streams.IncompleteReadError")
        return 0
    except OSError:
        logging.error("OSError")
        return 0


async def handleClients(reader, writer):
    for i in clients:
        if i[1] is None:
            i[1] = (reader, writer)
            await game(i[0],i[1])
            kill_game((i[0][1],i[1][1]))
            clients.remove(i)
            return
    clients.append([(reader,writer), None])



def serve_game(host, port):
    loop = asyncio.get_event_loop()
    routine = asyncio.start_server(handleClients, host, port, loop=loop)
    server = loop.run_until_complete(routine)
    print('Server Running on\nIP:', host, "\nPort:", port)
    try:
        loop.run_forever()
    except:
        pass
    finally:
        server.close()
        loop.run_until_complete(server.wait_closed())
        loop.close()

async def limit_client(host, port, loop, sem):
    async with sem:
        return await client(host, port, loop)

async def client(host, port, loop):
    """
    Run an individual client on a given event loop.
    You do not need to change this function.
    """
    try:
        reader, writer = await asyncio.open_connection(host, port, loop=loop)
        # send want game
        writer.write(b"\0\0")
        card_msg = await reader.readexactly(27)
        myscore = 0
        for card in card_msg[1:]:
            writer.write(bytes([Command.PLAYCARD.value, card]))
            result = await reader.readexactly(2)
            if result[1] == Result.WIN.value:
                myscore += 1
            elif result[1] == Result.LOSE.value:
                myscore -= 1
        if myscore > 0:
            result = "won"
        elif myscore < 0:
            result = "lost"
        else:
            result = "drew"
        logging.debug("Game complete, I %s", result)
        writer.close()
        return 1
    except ConnectionResetError:
        logging.error("ConnectionResetError")
        return 0
    except asyncio.streams.IncompleteReadError:
        logging.error("asyncio.streams.IncompleteReadError")
        return 0
    except OSError:
        logging.error("OSError")
        return 0

def main(args):
    """
    launch a client/server
    """
    host = args[1]
    port = int(args[2])
    if args[0] == "server":
        try:
            # your server should serve clients until the user presses ctrl+c
            serve_game(host, port)
        except KeyboardInterrupt:
            pass
        return
    else:
        loop = asyncio.get_event_loop()

    if args[0] == "client":
        loop.run_until_complete(client(host, port, loop))
    elif args[0] == "clients":
        sem = asyncio.Semaphore(1000)
        num_clients = int(args[3])
        clients = [limit_client(host, port, loop, sem)
                   for x in range(num_clients)]
        async def run_all_clients():
            """
            use `as_completed` to spawn all clients simultaneously
            and collect their results in arbitrary order.
            """
            completed_clients = 0
            for client_result in asyncio.as_completed(clients):
                completed_clients += await client_result
            return completed_clients
        res = loop.run_until_complete(
            asyncio.Task(run_all_clients(), loop=loop))
        logging.info("%d completed clients", res)

    loop.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main(sys.argv[1:])