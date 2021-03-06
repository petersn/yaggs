yaggs
=====

Yet Another Generic Game Server.

I had a relatively generic game server I wrote, but then I realized I wanted an even simpler, more generic one that could easily be talked to from C/C++, or other languages that are crummy at string processing.
Here's my even simpler one.

The protocol
------------

Open a TCP socket to the server on port 50321.
Initiailly, you are in no channels.
There are five commands you can send:

* `E <channel>`: Enters a given channel.
* `L <channel>`: Leaves a given channel.
* `M <channel> <message>`: Sends a given message to a given channel.
* `S <key> <value>`: Stores a key/value pair.
* `G <key>`: Retrieves a key/value pair.

Each time a string has to be encoded over the wire, it is sent as an 8-byte little endian length field, followed by the actual string.
Thus, to join the channel "foobar" one would send `"E\x06\0\0\0\0\0\0\0foobar"` to the server.
To send a message to this channel one could send `"M\x06\0\0\0\0\0\0\0foobar\x02\0\0\0\0\0\0\0hi"` to the server.
The server would then send the very same string (namely `"M\x06\0\0\0\0\0\0\0foobar\x02\0\0\0\0\0\0\0hi"`) to each client in the given channel.
When replying to the `G` command the server will either send back `"S"` followed by the key and value (that is to say, exactly the same data as was used to set the key), or send back `"E"` followed by an error string.
To quit, simply close your end of the socket.

