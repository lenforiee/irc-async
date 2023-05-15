from __future__ import annotations

import time
import asyncio
import logging

from enum import IntEnum

from typing import Optional
from typing import Callable
from typing import Awaitable
from typing import Any

AddressType = tuple[Any, int]
EventHandler = Callable[[], Awaitable[None]]

logging.basicConfig(level=logging.DEBUG)

SERVICE_URL = "irc.akatsuki.gg"
SERVICE_IRC_SUFFIX = "irc@akatsuki.gg"
BOT_NAME = "Aika"


def underscored_name(s: str) -> str:
    return s.replace(" ", "_")


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


class Client:
    def __init__(
        self,
        address: str,
        port: int,
        server: IRCServerAsync,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        self._server = server
        self._reader = reader
        self._writer = writer

        self._is_connected = True

        self.address = address
        self.port = port
        self.last_active = time.perf_counter()

        self.nick = ""
        self.safe_nick = ""
        self.irc_token = ""
        self.away_message = ""
        self.away_since = 0
        self.channels: set[Channel] = set()

    @property
    def address_tuple(self) -> AddressType:
        return self.address, self.port

    @property
    def irc_name(self) -> str:
        return f"{self.safe_nick}!{SERVICE_IRC_SUFFIX}"

    @property
    def irc_prefix(self) -> str:
        # TODO: `@` is for admins, `+` is for normal users
        return "@"

    @property
    def prefixed_safe_name(self) -> str:
        return self.irc_prefix + self.safe_nick

    def __str__(self) -> str:
        return self.irc_name

    async def send(self, message: str) -> None:
        self.last_active = time.perf_counter()

        logging.debug(f"{self.irc_name} {self.address_tuple} <- {message!r}")

        self._writer.write((message + "\r\n").encode())
        await self._writer.drain()

    async def send_irc_message(self, irc_code: IRCCommands, message: str) -> None:
        await self.send(f":{SERVICE_URL} {irc_code:03} {self.safe_nick} {message}")

    async def disconnect(self) -> None:
        self._is_connected = False
        self._writer.close()
        self._server.clients.pop(self.address_tuple)

        for channel in self.channels:
            await channel.part(self)

    async def receive(self) -> None:
        while self._is_connected:
            await asyncio.sleep(1)

            data = await self._reader.read(1024)  # should be enough

            if not data:
                continue

            self.last_active = time.perf_counter()

            msg_data = data.decode().strip()

            logging.debug(f"{self.irc_name} {self.address_tuple} -> {msg_data!r}")

            for line in msg_data.split("\n"):
                if not line:
                    continue

                command, *args = line.split(" ")

                handler = getattr(self, f"handle_{command.lower()}", None)
                if handler is not None:
                    await handler(*args)

    async def send_welcome_screen(self) -> None:
        await self.send_irc_message(
            IRCCommands.RPL_WELCOME, f":Welcome to the Akatsuki IRC!"
        )
        await self.send_irc_message(IRCCommands.RPL_MOTDSTART, ":-")

        for line_motd in self._server.motd:
            await self.send_irc_message(IRCCommands.RPL_MOTD, f":- {line_motd}")

        await self.send_irc_message(IRCCommands.RPL_ENDOFMOTD, ":-")

    async def notify_part_client(self, client: Client, channel: str) -> None:
        await self.send(
            f":{client.irc_name} PART :{channel}",
        )

    async def notify_join_client(self, client: Client, channel: str) -> None:
        await self.send(
            f":{client.irc_name} JOIN :{channel}",
        )

        match client.irc_prefix:
            case "@":
                await self.send(
                    f":{client.irc_name} MODE {channel} +o {client.safe_nick}",
                )
            case "+":
                await self.send(
                    f":{client.irc_name} MODE {channel} +v {client.safe_nick}",
                )

    async def part_channel(self, channel: str) -> None:
        chan = self._server.channels.get(channel)

        if chan is None:
            await self.send_irc_message(
                IRCCommands.ERR_NOSUCHCHANNEL, f"{channel} :No such channel {channel}"
            )
            return

        if chan not in self.channels or self not in chan.clients:
            await self.send_irc_message(
                IRCCommands.ERR_NOTONCHANNEL, f"{channel} :You're not on that channel"
            )
            return

        await chan.part(self)
        self.channels.remove(chan)

    async def join_channel(self, channel: str) -> None:
        chan = self._server.channels.get(channel)

        if chan is None:
            await self.send_irc_message(
                IRCCommands.ERR_NOSUCHCHANNEL, f"{channel} :No such channel {channel}"
            )
            return

        if self in chan.clients:
            await self.send_irc_message(
                IRCCommands.ERR_TOOMANYCHANNELS,
                f"{channel} :You're already on that channel",
            )
            return

        await chan.join(self)
        self.channels.add(chan)

        await self.handle_topic(channel)
        await self.handle_names(channel)

    async def handle_nick(self, *args) -> None:
        if not args:
            return

        nick = args[0].strip()
        self.nick = nick
        self.safe_nick = underscored_name(nick)

        await self.send_welcome_screen()

    async def handle_quit(self, *_) -> None:
        await self.disconnect()
        await self._server.broadcast(f":{self.irc_name} QUIT :quit")

    async def handle_ping(self, *args) -> None:
        self.last_active = time.perf_counter()

        ping_args = " ".join(args)
        await self.send(f":{SERVICE_URL} PONG {ping_args}")

    async def handle_pass(self, *args) -> None:
        if not args:
            return

        self.irc_token = args[0].strip()

    async def handle_who(self, *args) -> None:
        if not args:
            return

        channel = args[0].strip()
        await self.send_irc_message(
            IRCCommands.RPL_ENDOFWHO, f"{channel} :End of /WHO list."
        )

    async def handle_list(self, *_) -> None:
        await self.send_irc_message(IRCCommands.RPL_LISTSTART, "Channel :Users Name")

        for channel in tuple(self._server.channels.values()):
            await self.send_irc_message(
                IRCCommands.RPL_LIST,
                f"{channel.name} {len(channel)} :{channel.description}",
            )

        await self.send_irc_message(IRCCommands.RPL_LISTEND, ":End of /LIST")

    async def handle_privmsg(self, *args) -> None:
        if not args:
            return

        target = args[0].strip()
        message = " ".join(args[1:]).strip(":").strip()

        if not message:
            logging.debug(f"{self.nick} tried to send empty message to {target}")
            return

        if len(message) > 450:
            message = message[450:] + "... (message truncated)"

        # We don't want people to do shit like ()[Aika].
        message = message.replace("()[", "[")

        if target.startswith("#") or target.startswith("$"):
            channel = self._server.channels.get(target)
            if not channel:
                logging.debug(f"Did not found channel: {target}")
                return

            if not self in channel.clients:
                logging.debug(f"Did not found ourself in channel: {target}")
                return

            await channel.broadcast(
                f":{self.irc_name} PRIVMSG {channel.name} :{message}", self
            )
            return

        client = self._server.find_client_by_name(target)
        if not client:
            logging.debug(f"Did not found client: {target}")
            return

        if client.away_message:
            away_since = round(time.perf_counter() - client.away_since)
            await self.send_irc_message(
                IRCCommands.RPL_AWAY,
                f"{client.nick} {away_since} :{client.away_message}",
            )

        await client.send(f":{self.irc_name} PRIVMSG {client.safe_nick} :{message}")

    async def handle_away(self, *args) -> None:
        message = " ".join(args).strip(":")

        if not message or self.away_message:
            self.away_message = ""
            self.away_since = 0
            await self.send_irc_message(
                IRCCommands.RPL_UNAWAY, ":You are no longer marked as being away"
            )
            return

        self.away_message = message
        self.away_since = time.perf_counter()
        await self.send_irc_message(
            IRCCommands.RPL_NOWAWAY, ":You have been marked as being away"
        )

    async def handle_topic(self, *args) -> None:
        if not args:
            return

        channel = args[0].strip()
        chan = self._server.channels.get(channel)

        if not chan:
            await self.send_irc_message(
                IRCCommands.ERR_NOTONCHANNEL, f"{channel} :You're not on that channel"
            )
            return

        await self.send_irc_message(
            IRCCommands.RPL_TOPIC, f"{chan.name} :{chan.description}"
        )

        await self.send_irc_message(
            IRCCommands.RPL_TOPIC_INFO,
            f"{chan.name} {BOT_NAME}!{SERVICE_IRC_SUFFIX} {int(chan.creation_time)}",
        )

    async def handle_names(self, *args) -> None:
        if not args:
            return

        channel = args[0].strip()
        chan = self._server.channels.get(channel)

        if not chan:
            return

        for client in chan.clients:
            await self.send_irc_message(
                IRCCommands.RPL_NAMEREPLY, f"= {channel} :{client.prefixed_safe_name}"
            )

        await self.send_irc_message(
            IRCCommands.RPL_ENDOFNAMES, f"{channel} :End of /NAMES list."
        )

    async def handle_mode(self, *args) -> None:
        if not args:
            return

        target = args[0].strip()
        ourselves = underscored_name(target) == self.safe_nick
        channel = self._server.channels.get(target)

        if not ourselves and not channel:
            await self.send_irc_message(
                IRCCommands.ERR_USERSDONTMATCH, ":Can't change mode for other users"
            )
            return

        if ourselves:
            await self.send_irc_message(IRCCommands.RPL_UMODEIS, f"{self.nick} +i")
            return

        if channel is not None:
            await self.send_irc_message(IRCCommands.RPL_CHANNELMODEIS, f"{target} +nt")
            await self.send_irc_message(
                IRCCommands.RPL_CREATIONTIME, f"{target} {channel.creation_time}"
            )
            return

        mode = args[1]
        if not mode:
            return

        if mode.startswith("-"):
            return
        elif mode.startswith("+"):
            mode = mode[1:]

        prefixed_mode = mode[0]
        match prefixed_mode:
            case "b":
                await self.send_irc_message(
                    IRCCommands.RPL_ENDOFBANLIST, f"{target} :End of Channel Ban List"
                )
            case "i":
                await self.send(f":{self.irc_name} MODE {self.nick} :+i")

    async def handle_whois(self, *args) -> None:
        if not args:
            return

        name = args[0].strip()
        client = self._server.find_client_by_name(name)

        if client is None:
            await self.send_irc_message(
                IRCCommands.ERR_NOSUCHNICK, f"{name} :No such nick/channel"
            )
            return

        # TODO: use user id.
        user_url = f"https://akatsuki.gg/u/{client.safe_nick}"
        await self.send_irc_message(
            IRCCommands.RPL_WHOISUSER,
            f"{client.nick} {user_url} * :{user_url}",
        )

        await self.send_irc_message(
            IRCCommands.RPL_WHOISCHANNELS,
            f"{client.nick} :{' '.join(channel.name for channel in client.channels)}",
        )

        await self.send_irc_message(
            IRCCommands.RPL_WHOISSERVER,
            f"{client.nick} {SERVICE_URL} :Akatsuki IRC",
        )

        await self.send_irc_message(
            IRCCommands.RPL_ENDOFWHOIS, f"{client.nick} :End of /WHOIS list."
        )

    async def handle_part(self, *args) -> None:
        channel, *_ = " ".join(args).partition(" :")

        if channel.find(",") != -1:
            for chan in channel.split(","):
                await self.part_channel(chan)
        else:
            await self.part_channel(channel)

    async def handle_join(self, *args) -> None:
        channel, *_ = " ".join(args).partition(" :")

        if channel.find(",") != -1:
            for chan in channel.split(","):
                await self.join_channel(chan)
        else:
            await self.join_channel(channel)


class IRCServerAsync:
    def __init__(
        self,
        address: str,
        port: int,
        connection_timeout: int = 180,
    ) -> None:
        self.address = address
        self.port = port
        self.connection_timeout = connection_timeout
        self.motd: list[str] = []

        self._loop = asyncio.get_event_loop()
        self._server: Optional[asyncio.Server] = None

        self.clients: dict[AddressType, Client] = {}
        self.channels: dict[str, Channel] = {
            "#general": Channel(
                self,
                "#general",
                "Chat channel for general discussion!",
            )
        }

        self._closed = False

        # Events
        self._on_start: Optional[EventHandler] = None
        self._on_stop: Optional[EventHandler] = None

    async def _handle_upcoming_connection(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        address = writer.get_extra_info("peername")

        if address is None:
            return

        client = await self._ensure_client(address, reader, writer)

        logging.debug(f"{client.irc_name} {client.address_tuple} connected")
        self._loop.create_task(client.receive())

    async def _ensure_client(
        self,
        address: AddressType,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> Client:
        client = self.clients.get(address)

        if not client:
            client = Client(
                address=address[0],
                port=address[1],
                server=self,
                reader=reader,
                writer=writer,
            )
            self.clients[address] = client

        return client

    async def broadcast(self, message: str) -> None:
        for client in tuple(self.clients.values()):
            await client.send(message)

    def find_client_by_name(self, name: str) -> Optional[Client]:
        underscored = underscored_name(name)
        for client in tuple(self.clients.values()):
            if client.safe_nick == underscored:
                return client

        return None

    async def listen(self) -> None:
        server = await asyncio.start_server(
            lambda reader, writer: self._loop.create_task(
                self._handle_upcoming_connection(reader, writer)
            ),
            host=self.address,
            port=self.port,
        )

        self._server = server

        if self._on_start is not None:
            self._loop.create_task(self._on_start())  # type: ignore

        while not self._closed:
            await self._server.start_serving()

            current_time = time.perf_counter()
            await asyncio.sleep(1)

            # Remove inactive clients
            for client in tuple(self.clients.values()):
                if current_time - client.last_active > self.connection_timeout:
                    await client.disconnect()

                    await self.broadcast(
                        f":{client.irc_name} QUIT :ping timeout {self.connection_timeout} seconds"
                    )

        self._server.close()
        await self._server.wait_closed()

        self.clients.clear()

        if self._on_stop is not None:
            await self._on_stop()

    def stop(self) -> None:
        self._closed = True

    def start(self) -> None:
        with open("motd.txt", "r") as motd_file:
            self.motd = motd_file.readlines()

        self._loop.run_until_complete(self.listen())

    def on_start(self, handler: EventHandler) -> None:
        self._on_start = handler

    def on_stop(self, handler: EventHandler) -> None:
        self._on_stop = handler


# Pseudo channel for test purposes
class Channel:
    def __init__(
        self, server: IRCServerAsync, name: str, desc: str, destruct: bool = False
    ) -> None:
        self._server = server

        self.name = name
        self.destructable = destruct
        self.description: str = desc
        self.clients: set[Client] = set()
        self.creation_time = int(time.perf_counter())

    def __len__(self) -> int:
        return len(self.clients)

    async def broadcast(
        self, message: str, broadcaster: Client, include_sender: bool = False
    ) -> None:
        for client in self.clients:
            if not include_sender and client != broadcaster:
                await client.send(message)

    async def join(self, _client: Client) -> None:
        self.clients.add(_client)

        for client in self.clients:
            await client.notify_join_client(_client, self.name)

        # TODO: permission check.

    async def part(self, _client: Client) -> None:
        self.clients.remove(_client)

        for client in self.clients:
            await client.notify_part_client(_client, self.name)

        if self.destructable and not self.clients:
            self._server.channels.pop(self.name)


def main() -> int:
    server = IRCServerAsync("127.0.0.1", 6667)

    @server.on_start
    async def on_start() -> None:
        print("Server started")

    @server.on_stop
    async def on_stop() -> None:
        print("Server stopped")

    server.start()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
