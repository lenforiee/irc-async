from __future__ import annotations


import asyncio
from dataclasses import dataclass

from enum import IntEnum

import time
from typing import Any
from typing import Awaitable
from typing import Callable
from typing import Optional

AddressType = tuple[Any, int]
EventHandler = Callable[[], Awaitable[None]]


class IRCCommands(IntEnum):
    RPL_WELCOME = 1
    RPL_YOURHOST = 2
    RPL_CREATED = 3
    RPL_MYINFO = 4
    RPL_ISUPPORT = 5
    RPL_USERHOST = 302
    RPL_ISON = 303
    RPL_AWAY = 301
    RPL_UNAWAY = 305
    RPL_NOWAWAY = 306
    RPL_WHOISUSER = 311
    RPL_WHOISSERVER = 312
    RPL_WHOISOPERATOR = 313
    RPL_WHOISIDLE = 317
    RPL_ENDOFWHOIS = 318
    RPL_WHOISCHANNELS = 319
    RPL_WHOWASUSER = 314
    RPL_ENDOFWHOWAS = 369
    RPL_LISTSTART = 321
    RPL_LIST = 322
    RPL_LISTEND = 323
    RPL_UNIQOPIS = 325
    RPL_CHANNELMODEIS = 324
    RPL_CREATIONTIME = 329
    RPL_NOTOPIC = 331
    RPL_TOPIC = 332
    RPL_TOPIC_INFO = 333
    RPL_INVITING = 341
    RPL_SUMMONING = 342
    RPL_INVITELIST = 346
    RPL_ENDOFINVITELIST = 347
    RPL_EXCEPTLIST = 348
    RPL_ENDOFEXCEPTLIST = 349
    RPL_VERSION = 351
    RPL_WHOREPLY = 352
    RPL_ENDOFWHO = 315
    RPL_NAMEREPLY = 353
    RPL_ENDOFNAMES = 366
    RPL_LINKS = 364
    RPL_ENDOFLINKS = 365
    RPL_BANLIST = 367
    RPL_ENDOFBANLIST = 368
    RPL_INFO = 371
    RPL_ENDOFINFO = 374
    RPL_MOTDSTART = 375
    RPL_MOTD = 372
    RPL_ENDOFMOTD = 376
    RPL_YOUREOPER = 381
    RPL_REHASHING = 382
    RPL_YOURESERVICE = 383
    RPL_TIME = 391
    RPL_USERSSTART = 392
    RPL_USERS = 393
    RPL_ENDOFUSERS = 394
    RPL_NOUSERS = 395
    RPL_TRACELINK = 200
    RPL_TRACECONNECTING = 201
    RPL_TRACEHANDSHAKE = 202
    RPL_TRACEUNKNOWN = 203
    RPL_TRACEOPERATOR = 204
    RPL_TRACEUSER = 205
    RPL_TRACESERVER = 206
    RPL_TRACESERVICE = 207
    RPL_TRACENEWTYPE = 208
    RPL_TRACECLASS = 209
    RPL_TRACERECONNECT = 210
    RPL_TRACELOG = 261
    RPL_TRACEEND = 262
    RPL_LOCALUSERS = 265
    RPL_GLOBALUSERS = 266
    RPL_STATSCONN = 250
    RPL_STATSLINKINFO = 211
    RPL_STATSCOMMANDS = 212
    RPL_ENDOFSTATS = 219
    RPL_STATSUPTIME = 242
    RPL_STATSOLINE = 243
    RPL_UMODEIS = 221
    RPL_SERVLIST = 234
    RPL_SERVLISTEND = 235
    RPL_LUSERCLIENT = 251
    RPL_LUSEROP = 252
    RPL_LUSERUNKNOWN = 253
    RPL_LUSERCHANNELS = 254
    RPL_LUSERME = 255
    RPL_ADMINME = 256
    RPL_ADMINEMAIL = 259
    RPL_TRYAGAIN = 263
    ERR_NOSUCHNICK = 401
    ERR_NOSUCHSERVER = 402
    ERR_NOSUCHCHANNEL = 403
    ERR_CANNOTSENDTOCHAN = 404
    ERR_TOOMANYCHANNELS = 405
    ERR_WASNOSUCHNICK = 406
    ERR_TOOMANYTARGETS = 407
    ERR_NOSUCHSERVICE = 408
    ERR_NOORIGIN = 409
    ERR_NORECIPIENT = 411
    ERR_NOTEXTTOSEND = 412
    ERR_NOTOPLEVEL = 413
    ERR_WILDTOPLEVEL = 414
    ERR_BADMASK = 415
    ERR_UNKNOWNCOMMAND = 421
    ERR_NOMOTD = 422
    ERR_NOADMININFO = 423
    ERR_FILEERROR = 424
    ERR_NONICKNAMEGIVEN = 431
    ERR_ERRONEUSNICKNAME = 432
    ERR_NICKNAMEINUSE = 433
    ERR_NICKCOLLISION = 436
    ERR_UNAVAILRESOURCE = 437
    ERR_USERNOTINCHANNEL = 441
    ERR_NOTONCHANNEL = 442
    ERR_USERONCHANNEL = 443
    ERR_NOLOGIN = 444
    ERR_SUMMONDISABLED = 445
    ERR_USERSDISABLED = 446
    ERR_NOTREGISTERED = 451
    ERR_NEEDMOREPARAMS = 461
    ERR_ALREADYREGISTRED = 462
    ERR_NOPERMFORHOST = 463
    ERR_PASSWDMISMATCH = 464
    ERR_YOUREBANNEDCREEP = 465
    ERR_YOUWILLBEBANNED = 466
    ERR_KEYSET = 467
    ERR_CHANNELISFULL = 471
    ERR_UNKNOWNMODE = 472
    ERR_INVITEONLYCHAN = 473
    ERR_BANNEDFROMCHAN = 474
    ERR_BADCHANNELKEY = 475
    ERR_BADCHANMASK = 476
    ERR_NOCHANMODES = 477
    ERR_BANLISTFULL = 478
    ERR_NOPRIVILEGES = 481
    ERR_CHANOPRIVSNEEDED = 482
    ERR_CANTKILLSERVER = 483
    ERR_RESTRICTED = 484
    ERR_UNIQOPPRIVSNEEDED = 485
    ERR_NOOPERHOST = 491
    ERR_UMODEUNKNOWNFLAG = 501
    ERR_USERSDONTMATCH = 502
    RPL_SERVICEINFO = 231


class IRCServerAsync(asyncio.BaseProtocol):
    def __init__(
        self,
        address: str,
        port: int,
        connection_timeout: int = 180,
    ):
        self.address = address
        self.port = port
        self.connection_timeout = connection_timeout
        self.motd: list[str] = []

        self.channels: dict[str, Channel] = {
            "#general": Channel(
                self,
                "#general",
                "Chat channel for general discussion!",
            )
        }

        self._clients: dict[AddressType, Client] = {}
        self._server: Optional[asyncio.Server] = None
        self._loop = asyncio.get_event_loop()
        self._lock = asyncio.Lock()

        self._closed = False

        # Events
        self._on_start: Optional[EventHandler] = None
        self._on_stop: Optional[EventHandler] = None

    async def broadcast(self, message: str) -> None:
        async with self._lock:
            for client in self._clients.values():
                client.send(message)

    async def disconnect_inactive_clients(self) -> list[Client]:
        disconnected = []
        async with self._lock:
            for address, conn in self._clients.copy().items():
                if time.perf_counter() - conn.last_active > self.connection_timeout:
                    # use the real dict.
                    client = self._clients[address]
                    client.disconnect()
                    disconnected.append(client)

        return disconnected

    async def listen(self) -> None:
        loop = asyncio.get_running_loop()

        server = await loop.create_server(
            lambda: _ConnectionHandler(self),
            self.address,
            self.port,
        )
        self._server = server

        if self._on_start is not None:
            self._loop.create_task(self._on_start())  # type: ignore

        while not self._closed:
            current_time = time.perf_counter()
            await asyncio.sleep(1)

            disconnected = await self.disconnect_inactive_clients()
            for client in disconnected:
                await self.broadcast(
                    f":{client.identifier} QUIT :ping timeout {round(current_time - client.last_active)}s"
                )

        self._server.close()
        await self._server.wait_closed()

        self._clients.clear()

        if self._on_stop is not None:
            await self._on_stop()

    async def find_client_by_name(self, name: str) -> Optional[Client]:
        async with self._lock:
            for client in self._clients.values():
                if client.safe_nick == name.replace(" ", "_"):
                    return client

            return None

    def start(self) -> None:
        with open("motd.txt", "r") as motd_file:
            self.motd = motd_file.readlines()

        self._loop.run_until_complete(self.listen())

    def stop(self) -> None:
        self._closed = True

    def on_start(self, handler: EventHandler) -> EventHandler:
        self._on_start = handler
        return handler

    def on_stop(self, handler: EventHandler) -> EventHandler:
        self._on_stop = handler
        return handler


class Client:
    def __init__(
        self,
        server: IRCServerAsync,
        transport: asyncio.Transport,
        address: str,
        port: int,
    ):
        self._server = server
        self._transport = transport

        self.address = address
        self.port = port
        self.last_active = time.perf_counter()

        self.queue = bytearray()
        self.nick = ""
        self.safe_nick = ""
        self.password = ""
        self.away_message = ""
        self.away_since = 0
        self.channels: set[Channel] = set()

    @property
    def address_tuple(self) -> AddressType:
        return self.address, self.port

    @property
    def identifier(self) -> str:
        return f"{self.safe_nick}!irc@akatsuki.gg"

    @property
    def irc_prefix(self) -> str:
        # TODO: `@` is for admins, `+` is for normal users
        return "@"

    @property
    def prefixed_nick(self) -> str:
        return self.irc_prefix + self.safe_nick

    def __str__(self) -> str:
        return self.identifier

    def send(self, message: str) -> None:
        self.last_active = time.perf_counter()
        self._transport.write((message + "\r\n").encode())

    def disconnect(self) -> None:
        self._transport.close()
        self._server._clients.pop(self.address_tuple)

        for channel in self.channels:
            channel.client_part(self)

    async def receive(self, data: bytes) -> None:
        self.last_active = time.perf_counter()

        if not data:
            self.disconnect()
            return

        msg_data = data.decode().strip()

        for line in msg_data.split("\n"):
            if not line:
                continue

            print(line)

            command, *args = line.split(" ")

            handler = getattr(self, f"handle_{command.lower()}", None)
            if handler is not None:
                await handler(*args)

    def send_irc_msg(self, command: int, message: str) -> None:
        self.send(f":irc.akatsuki.gg {command:03} {self.safe_nick} {message}")

    def send_welcome_screen(self) -> None:
        self.send_irc_msg(IRCCommands.RPL_WELCOME, f":Welcome to the Akatsuki IRC!")
        self.send_irc_msg(IRCCommands.RPL_MOTDSTART, ":-")

        for line_motd in self._server.motd:
            self.send_irc_msg(IRCCommands.RPL_MOTD, f":- {line_motd}")

        self.send_irc_msg(IRCCommands.RPL_ENDOFMOTD, ":-")

    def send_ping(self) -> None:
        self.send(f"PING :irc.akatsuki.gg")

    def send_change_username(self, client: Client, new_username: str) -> None:
        self.send(
            f":{client.nick} NICK :{new_username}",
        )

    def send_part_channel(self, client: Client, channel: str) -> None:
        self.send(
            f":{client.identifier} PART :{channel}",
        )

    def send_join_channel(self, client: Client, channel: str) -> None:
        self.send(
            f":{client.identifier} JOIN :{channel}",
        )

        if client.irc_prefix == "+":
            self.send(
                f":Aika!irc@akatsuki.gg MODE {channel} +v {client.safe_nick}",
            )
        elif client.irc_prefix == "@":
            self.send(
                f":Aika!irc@akatsuki.gg MODE {channel} +o {client.safe_nick}",
            )

    async def part_other_channel(self, channel: str) -> None:
        if channel not in self._server.channels:
            self.send_irc_msg(
                IRCCommands.ERR_NOSUCHCHANNEL, f"{channel} :No such channel {channel}"
            )
            return

        chan = self._server.channels[channel]
        if chan not in self.channels:
            self.send_irc_msg(
                IRCCommands.ERR_NOTONCHANNEL, f"{channel} :You're not on that channel"
            )
            return

        if self not in chan.clients:
            self.send_irc_msg(
                IRCCommands.ERR_NOTONCHANNEL, f"{channel} :You're not on that channel"
            )
            return

        async with self._server._lock:
            chan.client_part(self)

        self.channels.remove(chan)

    async def join_other_channel(self, channel: str) -> None:
        if channel not in self._server.channels:
            self.send_irc_msg(
                IRCCommands.ERR_NOSUCHCHANNEL, f"{channel} :No such channel {channel}"
            )
            return

        chan = self._server.channels[channel]

        if self in chan.clients:
            self.send_irc_msg(
                IRCCommands.ERR_TOOMANYCHANNELS,
                f"{channel} :You're already on that channel",
            )
            return

        async with self._server._lock:
            chan.client_join(self)

        self.channels.add(chan)

        await self.handle_topic(channel)
        await self.handle_names(channel)

    async def handle_nick(self, msg: str, *_) -> None:
        self.nick = msg
        self.safe_nick = msg.replace(" ", "_")
        self.send_welcome_screen()
        # TODO: authentication

    async def handle_ping(self, *args) -> None:
        self.send(f":irc.akatsuki.gg PONG {' '.join(args)}")

    async def handle_pass(self, msg: str) -> None:
        self.password = msg

    async def handle_list(self, *_) -> None:
        self.send_irc_msg(IRCCommands.RPL_LISTSTART, "Channel :Users Name")
        for channel in self._server.channels.values():
            self.send_irc_msg(
                IRCCommands.RPL_LIST,
                f"{channel.name} {len(channel)} :{channel.description}",
            )
        self.send_irc_msg(IRCCommands.RPL_LISTEND, ":End of /LIST")

    async def handle_names(self, channel: str, *_) -> None:
        if channel not in self._server.channels:
            return

        chan = self._server.channels[channel]

        async with self._server._lock:
            for client in chan.clients:
                self.send_irc_msg(
                    IRCCommands.RPL_NAMEREPLY, f"= {channel} :{client.prefixed_nick}"
                )

        self.send_irc_msg(IRCCommands.RPL_ENDOFNAMES, f"{channel} :End of /NAMES list.")

    async def handle_who(self, channel: str, *_) -> None:
        self.send_irc_msg(IRCCommands.RPL_ENDOFWHO, f"{channel} :End of /WHO list.")

    async def handle_whois(self, name: str, *_) -> None:
        client = await self._server.find_client_by_name(name)
        if client is None:
            self.send_irc_msg(
                IRCCommands.ERR_NOSUCHNICK, f"{name} :No such nick/channel"
            )
            return

        # TODO: use user id.
        user_url = f"https://akatsuki.gg/u/{client.safe_nick}"
        self.send_irc_msg(
            IRCCommands.RPL_WHOISUSER,
            f"{client.nick} {user_url} * :{user_url}",
        )
        self.send_irc_msg(
            IRCCommands.RPL_WHOISCHANNELS,
            f"{client.nick} :{' '.join(channel.name for channel in client.channels)}",
        )
        self.send_irc_msg(
            IRCCommands.RPL_WHOISSERVER,
            f"{client.nick} irc.akatsuki.gg :Akatsuki IRC",
        )
        self.send_irc_msg(
            IRCCommands.RPL_ENDOFWHOIS, f"{client.nick} :End of /WHOIS list."
        )

    async def handle_topic(self, channel: str, *_) -> None:
        if channel not in self._server.channels:
            self.send_irc_msg(
                IRCCommands.ERR_NOTONCHANNEL, f"{channel} :You're not on that channel"
            )
            return

        chan = self._server.channels[channel]
        self.send_irc_msg(IRCCommands.RPL_TOPIC, f"{channel} :{chan.description}")
        self.send_irc_msg(
            IRCCommands.RPL_TOPIC_INFO,
            f"{channel} Aika!irc@akatsuki.gg {chan.creation_time}",
        )

    # TODO: this function probably needs rewrite
    async def handle_mode(self, *args) -> None:
        if len(args) < 1:
            return

        this_user = args[0].replace(" ", "_") == self.safe_nick
        chan = None
        if not this_user:
            chan = self._server.channels.get(args[0])

        if not this_user and not chan:
            self.send_irc_msg(
                IRCCommands.ERR_USERSDONTMATCH, ":Can't change mode for other users"
            )
            return

        if len(args) == 1:
            if this_user:
                self.send_irc_msg(IRCCommands.RPL_UMODEIS, f"{self.nick} +i")
            else:
                self.send_irc_msg(IRCCommands.RPL_CHANNELMODEIS, f"{args[0]} +nt")
                self.send_irc_msg(
                    IRCCommands.RPL_CREATIONTIME,
                    f"{args[0]} {chan.creation_time}",  # type: ignore
                )
        else:
            if not args[1]:
                return

            mode = args[1]
            if mode[0] == "-":
                # ignore - options
                return
            elif mode[0] == "+":
                # remove + for parsing
                if len(mode) == 1:
                    return

                mode = mode[1:]

            prefixed_mode = mode[0]
            if prefixed_mode == "b":
                self.send_irc_msg(
                    IRCCommands.RPL_ENDOFBANLIST,
                    f"{args[0]} :End of Channel Ban List",
                )
            elif prefixed_mode == "i":
                self.send(f":{self.identifier} MODE {self.nick} :+i")

    async def handle_privmsg(self, *args) -> None:
        target = args[0]
        message = " ".join(args).strip(":").strip()

        if not message:
            return

        if len(message) > 450:
            message = message[450:] + "... (message truncated)"

        # We don't want people to do shit like ()[Aika].
        message = message.replace("()[", "[")

        if target.startswith("#") or target.startswith("$"):
            channel = self._server.channels.get(target)
            if not channel:
                return

            if channel and not self in channel.clients:
                return

            await channel.broadcast(f":{self.identifier} PRIVMSG {message}", self)
        else:
            client = await self._server.find_client_by_name(target)
            if not client:
                return

            if client.away_message:
                self.send_irc_msg(
                    IRCCommands.RPL_AWAY,
                    f"{client.nick} {round(time.perf_counter() - client.away_since)} :{client.away_message}",
                )

            client.send(f":{self.identifier} PRIVMSG {message}")

    async def handle_away(self, *args) -> None:
        message = " ".join(args).strip(" :")

        if message:
            self.away_message = message
            self.away_since = time.perf_counter()
            self.send_irc_msg(
                IRCCommands.RPL_NOWAWAY, ":You have been marked as being away"
            )
        else:
            self.away_message = ""
            self.away_since = 0
            self.send_irc_msg(
                IRCCommands.RPL_UNAWAY, ":You are no longer marked as being away"
            )

    async def handle_part(self, *args) -> None:
        joined, *_ = " ".join(args).partition(" :")

        if joined.find(",") != -1:
            for channel in joined.split(","):
                await self.part_other_channel(channel)
        else:
            await self.part_other_channel(joined)

    async def handle_join(self, *args) -> None:
        joined, *_ = " ".join(args).partition(" :")

        if joined.find(",") != -1:
            for channel in joined.split(","):
                await self.join_other_channel(channel)
        else:
            await self.join_other_channel(joined)

    async def handle_quit(self, *_) -> None:
        self.disconnect()

        for client in self._server._clients.values():
            client.send(f":{self.identifier} QUIT :quit")


# Pseudo channel for test purposes
class Channel:
    def __init__(
        self, server: IRCServerAsync, name: str, desc: str, destruct: bool = True
    ) -> None:
        self._server = server

        self.name = name
        self.destructable = destruct
        self.description: str = desc
        self.clients: set[Client] = set()
        self.creation_time = time.time()

    def __len__(self) -> int:
        return len(self.clients)

    async def broadcast(
        self, message: str, sender: Client, include_sender: bool = False
    ) -> None:
        async with self._server._lock:
            for client in self.clients:
                if not include_sender and client != sender:
                    client.send(message)

    def client_join(self, _client: Client) -> None:
        self.clients.add(_client)

        for client in self.clients:
            client.send_join_channel(_client, self.name)

        # TODO: permission check.

    def client_part(self, _client: Client) -> None:
        self.clients.remove(_client)

        for client in self.clients:
            client.send_part_channel(_client, self.name)

        _client.send_part_channel(_client, self.name)

        # TODO: destruct channel if no users left


@dataclass
class _ConnectionHandler(asyncio.Protocol):
    _server: IRCServerAsync
    _transport: Optional[asyncio.Transport] = None
    _client: Optional[Client] = None

    def connection_made(self, transport: asyncio.Transport):
        self.transport = transport
        self._server._loop.create_task(self._ensure_client())

    def data_received(self, data: bytes) -> None:
        if self._client is not None:
            self._server._loop.create_task(self._client.receive(data))

    async def _ensure_client(self) -> Client:
        address = self.transport.get_extra_info("peername")
        client = self._server._clients.get(address)
        if client is None:
            async with self._server._lock:
                client = Client(
                    self._server,
                    self.transport,
                    address[0],
                    address[1],
                )
                self._server._clients[address] = client

        self._client = client
        return client


def main() -> int:
    server = IRCServerAsync(
        address="127.0.0.1",
        port=6667,
    )

    server.start()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
