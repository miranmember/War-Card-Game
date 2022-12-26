# War-Card-Game
This is a client-server implementation of the card game [War](https://en.wikipedia.org/wiki/War_(card_game)).
The game is played with a standard deck of 52 cards, and consists of two players. The server deals half of the deck, at random, to the two players (clients). Each player sends one of their cards to the server, and the server responds to each player with a "win," "lose," or "draw" message. In the event of a tie, neither player receives a "point" and play simply moves on to the next round. The game ends when all cards have been used and each client knows (based on the number of points they received) whether they won or they lost.
## Protocol
All WAR game messages follow the WAR message format, which consists of a one-byte "command" followed by either a one-byte payload or a 26-byte payload. The command values and their corresponding meanings are:

+ 0: Want game. This message should be sent by the client to request a game. The payload should always be the value 0.
+ 1: Game start. This message is sent by the server to both clients to start the game. The payload is a list of the client's cards, represented as integers from 0 to 51, representing the cards in a standard deck of cards.
+ 2: Play card. This message is sent by the client to the server to play a card. The payload is the index of the card in the client's hand.
+ 3: Play result. This message is sent by the server to both clients to communicate the result of a round. The payload is a single byte indicating the result, where 0 is a win, 1 is a draw, and 2 is a loss.

## Network Protocol
The WAR network protocol operates as follows:
1. The server listens for new TCP connections on a given port.
2. It waits until two clients have connected to that port.
3. Once both have connected, the clients send a message containing the "want game" command.
4. If both clients do this correctly, the server responds with a message containing the "game start" command, with a payload containing the list of cards dealt to that client.
5. The clients then send a message containing the "play card" command, with a payload indicating the card they wish to play.
6. The server responds to each client with a message containing the "play result" command, with a payload indicating the result of the round.
7. Steps 5 and 6 are repeated until all cards have been used.
8. The game ends and the clients disconnect.

## How to run
this runs a single client on ip address 127.0.0.1 and port 4444:
```
python war.py client 127.0.0.1 4444
```
This runs 1000 clients on ip 127.0.0.1 and port 444:
```
python war.py clients 127.0.0.1 444 1000
```

