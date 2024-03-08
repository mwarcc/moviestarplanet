import aiohttp, json
from moviestarplanet.entities import (
    MSP2ItemTemplate, Availability, ProfileAttributes, GetProfile,
    ProfileItem, ItemAdditionalData, Membership, Tag, Metadata,
    FindProfilesResponse, Actor, Node, Avatar
)
from datetime import datetime
from typing import List

class MovieStarPlanet2Async:
    """
    Interface for interacting with the MovieStarPlanet2 API.
    """

    def __init__(self, session: aiohttp.ClientSession = None, access_token: str = None, profileId: str = None) -> None:
        """
        Initializes a new instance of MovieStarPlanet2.

        Args:
            session (aiohttp.ClientSession, optional): HTTP client session. Defaults to None.
            access_token (str, optional): Access token. Defaults to None.
            profileId (str, optional): Profile ID. Defaults to None.
        """
        self.session = session
        self.access_token = access_token
        self.profileId = profileId
        self.headers = {'Authorization': f'Bearer {access_token}'}

    async def get_item_from_item_templates(self, objId: int) -> MSP2ItemTemplate:
        """
        Retrieves an MSP2ItemTemplate object from the API.

        Args:
            objId (int): Object ID.

        Returns:
            MSP2ItemTemplate: MSP2ItemTemplate object.
        """
        async with self.session.get(f"https://eu.mspapis.com/curatedcontentitemtemplates/v2/item-templates/{objId}", headers=self.headers) as response:
            data = await response.json()
            return MSP2ItemTemplate(**{key: data.get(key) for key in MSP2ItemTemplate.__init__.__code__.co_varnames if key in data})
        
    async def check_username_availability_async(self, username: str, culture: str, gameId: str = "j68d") -> Availability:
        """
        Checks the availability of a username asynchronously.

        Args:
            username (str): The username to check availability for.
            culture (str): The culture.
            gameId (str, optional): The game ID. Defaults to "j68d".

        Returns:
            Availability: An Availability object representing the availability status.
        """
        async with self.session.get(f"https://eu.mspapis.com/profileidentity/v1/profiles/names/availability?gameId={gameId}&name={username}&culture={culture}") as response:
            data = await response.json()
            return Availability(**{key: data.get(key) for key in Availability.__init__.__code__.co_varnames if key in data})
        
    async def get_attributes_async(self, profileId: str = None) -> ProfileAttributes:
        """
        Retrieves profile attributes asynchronously.

        Args:
            profileId (str, optional): Profile ID. Defaults to None.

        Returns:
            ProfileAttributes: Profile attributes object.
        """
        profileId = self.profileId if profileId is None else profileId
        async with self.session.get(f"https://eu.mspapis.com/profileattributes/v1/profiles/{profileId}/games/j68d/attributes", headers=self.headers) as response:
            if response.status == 200:
                data = await response.json()
                return ProfileAttributes(**data)
            return ProfileAttributes()
    
    async def _get_attributes_json_async(self, profileId: str = None) -> dict:
        profileId = self.profileId if profileId is None else profileId
        async with self.session.get(f"https://eu.mspapis.com/profileattributes/v1/profiles/{profileId}/games/j68d/attributes", headers=self.headers) as response:
            if response.status == 200:
                data = await response.json()
                return data
            return None
        
    async def get_profiles_async(self, profileIds: list) -> GetProfile:
        """
        Retrieves profiles asynchronously based on provided profile IDs.

        Args:
            profileIds (list): List of profile IDs to retrieve profiles for.

        Returns:
            GetProfile: GetProfile object containing the retrieved profile data.
        """
        json_data = {
            'query': 'query GetProfiles($profileIds: [String!]!, $gameId: String!){ profiles(profileIds: $profileIds){ id name culture avatar(preferredGameId: $gameId){ gameId face full } membership {currentTier lastTierExpiry } } }',
            'variables': '{"profileIds":'+json.dumps(profileIds)+',"gameId":"j68d"}',
        }
        async with self.session.post("https://eu.mspapis.com/edgerelationships/graphql/graphql", json=json_data, headers=self.headers) as response:
            if response.status == 200:
                data = await response.json()
                return GetProfile(data)
            return GetProfile()
        
    async def get_inventory_async(self, profileId: str = None) -> List[ProfileItem]:
        """
        Asynchronously fetches the inventory items for a given profile ID.

        Args:
            profileId (str, optional): The profile ID for which to fetch the inventory items. If None, uses the default profile ID. Defaults to None.

        Returns:
            List[ProfileItem]: A list of ProfileItem objects representing the inventory items.
        """
        profileId = self.profileId if profileId is None else profileId
        async with self.session.get(f"https://eu.mspapis.com/profileinventory/v1/profiles/{profileId}/games/j68d/inventory/items?&page=1&pageSize=100", headers=self.headers) as response:
            if response.status == 200:
                data = await response.json()
                inventory = []
                for item_data in data:
                    additional_data = ItemAdditionalData(NebulaData=item_data.get("additionalData", {}))
                    item = ProfileItem(
                        id=item_data["id"],
                        objectId=item_data["objectId"],
                        itemId=item_data["itemId"],
                        objectSource=item_data["objectSource"],
                        itemSource=item_data["itemSource"],
                        metadata=Metadata(**item_data["metadata"]),
                        additionalData=additional_data,
                        tags=[Tag(**tag_data) for tag_data in item_data["tags"]]
                    )
                    inventory.append(item)
                return inventory
            return []
          
    
    async def search_profiles_async(self, username: str, server: str) -> FindProfilesResponse:
        """
        Asynchronous profile search.

        Args:
            username (str): The username to search for.
            server (str): The server on which to perform the search.

        Returns:
            FindProfilesResponse: The response object containing the found profiles.
        """
        json_data = {
            'query': 'query GetProfileSearch($region: String!, $startsWith: String!, $pageSize: Int, $currentPage: Int, $preferredGameId: String!) { findProfiles(region: $region, nameBeginsWith: $startsWith, pageSize: $pageSize, page: $currentPage) { totalCount nodes { id avatar(preferredGameId: $preferredGameId) { gameId face full } } } }',
            'variables': {'region': server, 'startsWith': username, 'pageSize': 50, 'currentPage': 1, 'preferredGameId': 'j68d'},
        }
        async with self.session.post("https://eu.mspapis.com/edgerelationships/graphql/graphql", json=json_data, headers=self.headers) as response:
            if response.status == 200:
                data = await response.json()
                nodes = []
                for node in data['data']['findProfiles']['nodes']:
                    avatar_data = node['avatar']
                    if avatar_data is not None:
                        gameId = avatar_data.get('gameId')
                        face = avatar_data.get('face')
                        full = avatar_data.get('full')
                        avatar = Avatar(gameId=gameId, face=face, full=full)
                        nodes.append(Node(id=node['id'], avatar=avatar))
                    else:
                        pass
                find_profiles_response = FindProfilesResponse(
                    totalCount=data['data']['findProfiles']['totalCount'],
                    nodes=nodes
                )
                return find_profiles_response
            return FindProfilesResponse(totalCount=0, nodes=[])
        
    async def set_mood_async(self, mood: str) -> bool:
        """
        Asynchronously sets user current mood and updates the profile attributes.

        returns True or False if the set was successfully set.
        """
        """"""
        attributes = await self._get_attributes_json_async(profileId=self.profileId)
        if attributes != None:
            attributes["additionalData"]["Mood"] = mood
            return bool(attributes) and (await self.session.put(f'https://eu.mspapis.com/profileattributes/v1/profiles/{self.profileId}/games/j68d/attributes', json=attributes, headers=self.headers)).status == 200
    
    async def swap_gender_async(self) -> bool:
        """
        Asynchronously swaps the gender and updates the profile attributes.

        returns True or Fale if the swap was successful.
        """
        """"""
        attributes = await self._get_attributes_json_async(profileId=self.profileId)
        return bool(attributes) and (await self.session.put(url=f'https://eu.mspapis.com/profileattributes/v1/profiles/{self.profileId}/games/j68d/attributes', json=attributes, headers=self.headers)).status == 200
    
    async def send_autograph_async(self, profileId: str) -> bool:
        """
        Asynchronously sends an autograph to the specified profile.

        Args:
            profileId (str): The ID of the profile to send the autograph to.

        Returns:
            bool: True if the autograph was sent successfully, False otherwise.
        """
        jsonData = {'greetingType': "autograph", 'receiverProfileId': profileId, 'compatibilityMode': "Nebula", 'useAltCost': False, 'ignoreDailyCap': True}
        async with self.session.post("https://eu.mspapis.com/profilegreetings/v1/profiles/" + self.profileId + "/games/j68d/greetings", json=jsonData, headers=self.headers) as response: return 'Succeeded' in await response.text()
