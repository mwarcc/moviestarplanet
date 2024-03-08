import asyncio
import atexit
import binascii
import hashlib
import random
import logging
from typing import Optional, Any, List

import pyamf
from pyamf import remoting, AMF3, amf3
from aiohttp import TCPConnector, ClientSession, ClientTimeout, ClientResponse
from dataclasses import fields

from moviestarplanet.conditions import requires_login
from moviestarplanet.enums import MspServer
from moviestarplanet.entities import AMFResult, HashSaltPreset, LoginResult, LoginStatus, NebulaLoginStatus, Actor, AwardData, PiggyBank, SearchActor, Autograph, Message
from moviestarplanet.proxy import proxy_to_be_used
from moviestarplanet import uritransform
from moviestarplanet import checksum, histogram
from moviestarplanet.exceptions import *
from moviestarplanet.nebula import MovieStarPlanet2Async
from moviestarplanet import mspsocket
from threading import Lock
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem
from binascii import hexlify

def random_ipv4():
    ip = ".".join(map(str, (random.randint(0, 255) 
                            for _ in range(4))))
    return ip


def random_user_agent():
    software_names = [SoftwareName.CHROME.value]
    operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]   

    user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems, limit=100)
    return  user_agent_rotator.get_random_user_agent()


class Authorization:
    """Class needed to authorize requests which need TicketHeader attribute to be used."""

    def __init__(self, parent: Any) -> None:
        self.parent: Any = parent
        self.local_bytes: bytes = b''
        self.marking_id: int = 0
        self.lock: Lock = Lock()

    def increment_marking_id(self) -> None:
        """Increments the `marking_id` attribute by 1 in a thread-safe manner."""
        with self.lock:
            self.marking_id += 1

    def get_local_bytes(self) -> None:
        """
        Increments the marking ID and converts it to bytes in the UTF-8 encoding.
        """
        self.increment_marking_id()
        self.local_bytes = str(self.marking_id).encode('utf-8')

    def md5(self) -> str:
        """
        Calculate the MD5 hash of the local bytes.
        """
        return hashlib.md5(self.local_bytes).hexdigest()

    def hexlify(self) -> str:
        """
        Converts the given byte array to a hexadecimal string representation.
        """
        return binascii.hexlify(self.local_bytes).decode()

    def ticket_header(self) -> Any:
        """Returns the updated `TicketHeader` attribute as an ASObject."""
        self.get_local_bytes()
        ticket_header_value = self.parent.ticket + self.md5() + self.hexlify()
        return pyamf.ASObject({"Ticket": ticket_header_value, "anyAttribute": None})


class MovieStarPlanetAsync:
    def __init__(self, ticket: Optional[str] = None, timeout: Optional[int] = 10, ssl: bool = False, ensure_https: Optional[bool]=True, retry_delay: Optional[int]=0, retry_attempts: Optional[int]=2, proxy: Optional[str]=None,  hashSaltPreset: Optional[HashSaltPreset]=HashSaltPreset(),  user_agent: Optional[str]=random_user_agent(), raise_exception_on_timeout: Optional[bool]=True, logging_level: Optional[int]=0, raise_exception_on_request_exception: Optional[bool]=False):
        self._session: ClientSession = ClientSession(connector=TCPConnector(ssl=ssl), timeout=ClientTimeout(total=timeout))
        self.ticket: Optional[str] = ticket
        self.timeout: Optional[int] = timeout
        self.authorizer = Authorization(parent=self)
        self.ensure_https: Optional[bool] = ensure_https
        self.retry_delay, self.retry_attempts = retry_delay, retry_attempts
        self.proxy = proxy
        self.hashSaltPreset = hashSaltPreset
        self.headers: dict = {'User-Agent': user_agent, 'Referer': 'app:/cache/t1.bin/[[DYNAMIC]]/2', 'Content-Type': 'application/x-amf', 'True-Client-IP': random_ipv4()}
        self.raise_exception_on_timeout: Optional[bool] = raise_exception_on_timeout
        self.raise_exception_on_request_exception: Optional[bool] = raise_exception_on_request_exception
        self.logging_level: Optional[int] = logging_level
        self.access_token: str = None
        self.nebula = MovieStarPlanet2Async()
        self.websocket = mspsocket.MspSocketUser()

        atexit.register(self.close_session)

    def close_session(self):
        """
        Close the aiohttp session when the program exits.
        """
        if getattr(self, '_session', None) is not None:
            asyncio.run(self._session.close())

    @requires_login
    def ticket_header(self) -> pyamf.ASObject:
        """Returns the updated `TicketHeader` attribute as an ASObject."""
        return self.authorizer.ticket_header()
    
    def _fix_proxy(self, proxy: str) -> str | None:
        """
        Fixes the proxy format to ensure it starts with 'http://' if not None.

        Args:
            proxy (str): The proxy string to fix.

        Returns:
            str | None: The fixed proxy string or None if proxy is None.
        """
        return proxy if proxy is None or proxy.startswith("http") else f'http://{proxy}'

    async def send_command_async(self, server: MspServer, method: str, params: list, proxy: Optional[str]=None) -> AMFResult:
        """
        Sends a command asynchronously to the specified server using the specified method and parameters.

        Args:
            server (MspServer): The target server to send the command to.
            method (str): The method to call on the server.
            params (list): The parameters to pass to the method.
            proxy (Optional[str]): The proxy to be used for the request, if any.

        Returns:
            AMFResult: The result of the command execution, wrapped in an AMFResult object.

        Notes:
            This function sends a command asynchronously using the specified method and parameters to the given server.
            It handles retries based on the configured retry attempts and delay.
            If a proxy is specified, it will be used for the request.
        """
        proxy = proxy_to_be_used(self, proxy)
        url = uritransform.match_(f"https://ws-{server}.mspapis.com/Gateway.aspx?method={method}", self.ensure_https)

        request = remoting.Request(target=method, body=params)
        envelope = remoting.Envelope(AMF3)
        envelope.headers = remoting.HeaderCollection({
            ("sessionID", False, histogram.get_session_id()),
            ("needClassName", False, False),
            ("id", False, checksum.calculate_checksum(arguments=params, hashSet=self.hashSaltPreset))
        })
        envelope['/1'] = request
        encoded_request = remoting.encode(envelope).getvalue()

        for _ in range(self.retry_attempts+1):
            ins = await self._send_request(self._session, url, encoded_request, proxy)
            if ins.status_code != -0: return ins
            await asyncio.sleep(self.retry_delay)

        return await self._send_request(self._session, url, encoded_request, proxy)

    
    async def _send_request(self, session, url, encoded_request, proxy) -> AMFResult:
        """
        Sends an HTTP POST request asynchronously using aiohttp.

        Args:
            session (ClientSession): The aiohttp session to use for the request.
            url (str): The URL to send the request to.
            encoded_request (bytes): The encoded request data.
            proxy (str): The proxy to use for the request.

        Returns:
            AMFResult: AMF Result
        """
        try:
            async with session.post(url, data=encoded_request, proxy=self._fix_proxy(proxy),
                                    timeout=ClientTimeout(total=self.timeout), headers=self.headers) as response:
                return await self._parse_response(response)
        except asyncio.TimeoutError:
            if self.logging_level == 1:
                logging.critical(f"Server timeout to {url}")

            if self.raise_exception_on_timeout:
                raise TimeoutError()
            
            return AMFResult(bytes_data=None, status_code=-1)
        except Exception as e:
            if self.logging_level == 1:
                logging.error(f"Error sending request to {url}: {e}")
            if self.raise_exception_on_request_exception:
                raise
            return AMFResult(bytes_data=None, status_code=-1)

    async def _parse_response(self, response: ClientResponse):
        """
        Parses the HTTP response from the server.

        Args:
            response (ClientResponse): The response from the server.

        Returns:
            AMFResult: The parsed result of the response.
        """
        return AMFResult(bytes_data=await response.read(), status_code=response.status)
    
    async def login_async(self, username: str, password: str, server: MspServer, proxy: str = None, websocket: bool = True) -> LoginResult:
        """
        An asynchronous function for logging in with the provided username, password, server, and optional proxy.
        Returns LoginResult.

        for "Actor" and "nebulaLoginStatus" please use a ["Key"] to get value.
        """
        response = await self.send_command_async(
            server=server,
            method='MovieStarPlanet.WebService.User.AMFUserServiceWeb.Login',
            params=[username, password, [], None, None, "MSP1-Standalone:XXXXXX"],
            proxy=proxy
        )
    
        extract_login_status = lambda response: LoginStatus(
            **{key: value for key, value in response.content.get('loginStatus', {}).items() if key in {field.name for field in fields(LoginStatus)}}
        ) if response.status_code == 200 else LoginStatus()

        login = LoginResult(loginStatus=extract_login_status(response)) if response.status_code == 200 else LoginResult(loginStatus=LoginStatus())

        if login.loginStatus.status in {'ThirdPartyCreated', 'Success'}:
            self.ticket, self.actor_id, self.server, self.username = login.loginStatus.ticket, login.loginStatus.ActorId, server, username
            self.access_token = login.loginStatus.nebulaLoginStatus['accessToken']
            self.nebula = MovieStarPlanet2Async(session=self._session, access_token=self.access_token, profileId=login.loginStatus.nebulaLoginStatus['profileId'])
            
            if websocket == True:
                try:
                    await self.websocket.connect(server=server)
                    await self.websocket.send_authentication(server=server, access_token=self.access_token, profile_id=login.loginStatus.nebulaLoginStatus['profileId'])
                except:
                    if self.logging_level == 1:
                        logging.critical("Could not connect to websocket.")
        return login
    
    @requires_login
    async def claim_reward_async(self, award_type: str, proxy: Optional[str]=None) -> AwardData:
        """
        Claims a reward asynchronously.

        Args:
            award_type (str): The type of award to claim.

        Returns:
            AwardData: An instance of AwardData representing the claimed reward.
        """
        response = await self.send_command_async(server=self.server, method="MovieStarPlanet.WebService.Achievement.AMFAchievementWebService.ClaimReward", params=[
            self.ticket_header(), award_type, int(self.ticket.split(",")[1])
        ], proxy=proxy)
        return AwardData(**response.content.get("Data")) if response.status_code == 200 and response.content.get("Data") else AwardData()
    
    @requires_login
    async def block_user_async(self, actorId: int, proxy: Optional[int]=None) -> bool:
        """
        Asynchronously blocks a user.

        Parameters:
            - actorId (int): The ID of the user to be blocked.
            - proxy (Optional[int]): Proxy identifier for the request (default is None).

        Returns:
            - bool: True if the user is successfully blocked, False otherwise.
        """
        response = await self.send_command_async(server=self.server, method="MovieStarPlanet.WebService.ActorService.AMFActorServiceForWeb.BlockActor", params=[
            self.ticket_header(), int(self.ticket.split(",")[1]), int(actorId)
        ], proxy=proxy)
        return True if response.status_code == 200 and response.content == 0 else False
    
    @requires_login
    async def get_piggy_bank_async(self, proxy: Optional[int]=None) -> PiggyBank:
        """
        Asynchronously retrieves information about the user's piggy bank.

        Parameters:
        - proxy (Optional[int]): Proxy identifier for the request (default is None).

        Returns:
        - PiggyBank: An object containing information about the user's piggy bank.
        """
        response = await self.send_command_async(server=self.server, method="MovieStarPlanet.WebService.PiggyBank.AMFPiggyBankService.GetPiggyBank", params=[
            self.ticket_header()
        ], proxy=proxy)
        return PiggyBank(**response.content.get("Data")) if response.status_code == 200 and response.content.get("Data") else PiggyBank()
    
    @requires_login
    async def search_actor_by_name_async(self, name: str, proxy: Optional[int]=None) -> List['SearchActor']:
        """
        Asynchronously searches for actors by name.

        Parameters:
            - name (str): The name of the actor to search for.
            - proxy (Optional[int]): Proxy identifier for the request (default is None).

        Returns:
            - List[SearchActor]: A list of SearchActor objects representing the search results.
        """
        response = await self.send_command_async(server=self.server, method="MovieStarPlanet.WebService.ActorService.AMFActorServiceForWeb.SearchActorByNameNeb", params=[
            self.ticket_header(), int(self.ticket.split(",")[1]), name
        ], proxy=proxy)
        xtract_search_actors = lambda response: [SearchActor(**{key: value for key, value in actor.items() if key in {field.name for field in fields(SearchActor)}}) for actor in response.content] if response.status_code == 200 else []

        if response.status_code == 200:
            return xtract_search_actors(response)
        return []
 
    
    @requires_login
    async def recycle_item_async(self, item_rel_id: int = 0, actor_click_item: int = 0, proxy: Optional[int] = None) -> bool:
        """
        Recycles an item asynchronously.

        Parameters:
            item_rel_id (int): The item rel ID of the item to recycle.
            actor_click_item (int): The bonster/pet rel id to recycle.
            proxy (Optional[int]): Proxy server identifier, if any.

        Returns:
            bool: True if the item is recycled successfully, False otherwise.
        """
        response = await self.send_command_async(server=self.server, method="MovieStarPlanet.WebService.Profile.AMFProfileService.RecycleItem", params=[
            self.ticket_header(), int(self.ticket.split(",")[1]), int(item_rel_id), int(actor_click_item)
        ], proxy=proxy)
        return True if response.status_code == 200 and int(response.content) > 0 else False
    
    @requires_login
    async def send_autograph_async(self, actorId: int, proxy: Optional[int] = None) -> Autograph:
        """
        Sends an autograph to the specified actor asynchronously.

        Parameters:
            - actorId (int): The ID of the actor to send the autograph to.
            - proxy (Optional[int]): The optional proxy ID to use for the request.

        Returns:
            - Autograph: An Autograph object containing the result of the operation.
        """
        response = await self.send_command_async(server=self.server, method="MovieStarPlanet.WebService.UserSession.AMFUserSessionService.GiveAutographAndCalculateTimestamp", params=[
            self.ticket_header(), int(self.ticket.split(",")[1]), int(actorId)
        ], proxy=proxy)
        return Autograph(**response.content) if response.status_code == 200 else Autograph()
    
    @requires_login
    async def create_snapshot_small_and_big_mobile_async(self, image_data_small: amf3.ByteArray, image_data_big: amf3.ByteArray, proxy: Optional[int] = None) -> bool:
        """
        Creates a profile snapshot with both small and big images asynchronously for mobile devices.

        Parameters:
            - image_data_small (amf3.ByteArray): The image data for the small snapshot.
            - image_data_big (amf3.ByteArray): The image data for the big snapshot.
            - proxy (Optional[int]): The optional proxy ID to use for the request.

        Returns:
           - bool: True if the snapshot creation is successful, False otherwise.
        """
        response = await self.send_command_async(server=self.server, method="MovieStarPlanet.MobileServices.AMFGenericSnapshotService.CreateSnapshotSmallAndBig", params=[
            self.ticket_header(), int(self.ticket.split(",")[1]), "moviestar", "fullSizeMovieStar", image_data_small, image_data_big, "jpg"
        ], proxy=proxy)
        return response.content if response.status_code == 200 else False

    