from dataclasses import dataclass
from typing import Union
from pyamf import remoting
from dataclasses import dataclass, field
from typing import Union, Optional
import datetime
from typing import Dict, Any, List

@dataclass
class HashSaltPreset:
    salt: str = "2zKzokBI4^26#oiP"
    no_ticket_value: str = "XSV7%!5!AX2L8@vn"
    
@dataclass
class AMFResult:
    bytes_data: bytes
    status_code: int 

    @property
    def content(self) -> Union[list, dict]:
        try:
            return remoting.decode(self.bytes_data)["/1"].body
        except:
            return None
    
    @property
    def code(self) -> Union[int, None]:
        if isinstance(self.content, dict): return self.content.get('Code')
        return None
    
    @property
    def rateLimited(self) -> bool:
        return self.status_code == 500
    
@dataclass
class Actor:
    ActorId: int = 0
    Level: int = 0
    Name: str = None
    SkinSWF: str = None
    SkinColor: str = None
    NoseId: int = 0
    EyeId: int = 0
    MouthId: int = 0
    Money: int = 0
    EyeColors: str = None
    MouthColors: str = None
    Fame: int = 0
    Fortune: int = 0
    FriendCount: int = 0
    Created: datetime = datetime.datetime.utcnow()
    LastLogin: datetime = datetime.datetime.utcnow()
    Moderator: int = 0
    ProfileDisplays: int =0
    IsExtra: int = 0
    ValueOfGiftsReceived: int = 0
    ValueOfGiftsGiven: int = 0
    NumberOfGiftsGiven: int = 0
    NumberOfGiftsReceived: int = 0
    NumberOfAutographsReceived: int = 0
    NumberOfAutographsGiven: int = 0
    TimeOfLastAutographGiven: datetime = datetime.datetime.utcnow()
    BoyfriendId: int = None
    MembershipPurchasedDate: datetime = datetime.datetime.utcnow()
    MembershipTimeoutDate: datetime = datetime.datetime.utcnow()
    MembershipGiftRecievedDate: datetime = datetime.datetime.utcnow()
    BehaviourStatus: int = 0
    LockedUntil: datetime = datetime.datetime.utcnow()
    LockedText: str = None
    BadWordCount: int = 0
    PurchaseTimeoutDate: datetime = datetime.datetime.utcnow()
    EmailValidated: int = 0
    RetentionStatus: int = 0
    GiftStatus: int = 0
    MarketingNextStepLogins: int = 0
    MarketingStep: int = 0
    TotalVipDays: int = 0
    RecyclePoints: int = 0
    EmailSettings: int = 0
    TimeOfLastAutographGivenStr: datetime = datetime.datetime.utcnow()
    FriendCountVIP: int = 0
    ForceNameChange: int = 0
    CreationRewardStep: int = 0
    CreationRewardLastAwardDate: datetime = datetime.datetime.utcnow()
    NameBeforeDeleted: str = None
    LastTransactionId: int = 0
    AllowCommunication: int = 1
    Diamonds: int = 0
    PopUpStyleId: int = 0
    EyeShadowId: int = 0
    EyeShadowColors: str = None
    RoomLikes: int = 0
    Email: str = None


@dataclass
class NebulaLoginStatus:
    accessToken: Optional[str] = None
    profileId: Optional[str] = None
    refresh_token: Optional[str] = None

@dataclass
class LoginStatus:
    def default_nebula_login_status():
        return NebulaLoginStatus()

    status: str = None
    userType: str = None
    userIp: int = -1
    ticket: str = None
    boughtRespinToday: bool = False
    diamondRespinPrice: int = 0
    fameWheelSpinPrice: int = 0
    wheelDownloadableFameSpins: int = 0
    nebulaLoginStatus: NebulaLoginStatus = field(default_factory=default_nebula_login_status)
    actor: Actor = field(default_factory=Actor)

    @property
    def isLoggedIn(self) -> bool:
        return self.status in {'Success', 'ThirdPartyCreated'}
    
    @property
    def ActorId(self) -> int:
        return int(self.ticket.split(',')[1]) if self.ticket != None else None

@dataclass
class LoginResult:
    loginStatus: LoginStatus = field(default_factory=LoginStatus)

@dataclass
class RandomCredentials:
    username: str
    password: str 
    server: str

@dataclass
class MSP2ItemTemplate:
    nameResourceIdentifier: str = None
    lookUpId: str = None
    id: str = None
    graphicsResourceIdentifier: str = None
    created = datetime.datetime

@dataclass
class AwardData:
    Starcoins: int = 0
    Diamonds: int = 0
    Fame: int = 0

@dataclass
class PiggyBank:
    StarCoins: int = 0
    Diamonds: int = 0
    Fame: int = 0
    PiggyBankState: int = 0

@dataclass
class SearchActor:
    ActorId: int = 0
    ProfileId: str = None
    MembershipTimeoutDate: datetime.datetime = datetime.datetime.utcnow()
    Status: int = 0
    Name: str = None
    Level: int = 0
    IsVIP: bool = False
    
dataclass
class Availability:
    isAllowed: bool = False
    isAvailable: bool = False
    nameSuggestions: list = field(default_factory=list)

@dataclass
class AdditionalData:
    ProfilePopupCustomization: str = None
    Mood: str = None
    WelcomeVersion: str = None
    ChatRoomPositionData: str = None
    Gender: str = None
    DefaultMyHome: str = None
    WAYD: str = None
    UnlockedFeatures: str = None

@dataclass
class ProfileAttributes:
    profileId: str = None
    gameId: str = None
    avatarId: str = None
    additionalData: AdditionalData = field(default_factory=AdditionalData)


@dataclass
class Avatar:
    gameId: str = None
    face: str = None
    full: str = None

@dataclass
class Membership:
    currentTier: str = None
    lastTierExpiry: datetime = None

@dataclass
class Profile:
    id: str = None
    name: str = None
    culture: str = None
    avatar: Avatar = None
    membership: Membership = None

@dataclass
class GetProfile:
    data: dict

    @property
    def profiles(self) -> List[Profile]:
        profile_dicts = self.data.get('data', {}).get('profiles', [])
        return [Profile(
            id=profile.get('id'),
            name=profile.get('name'),
            culture=profile.get('culture'),
            avatar=Avatar(**profile.get('avatar', {})),
            membership=Membership(**profile.get('membership', {}))
        ) for profile in profile_dicts]
    


@dataclass
class ItemAdditionalData:
    NebulaData: Dict[str, str]
    extra_data: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.NebulaData, dict):
            raise TypeError("NebulaData must be a dictionary")

        if not isinstance(self.extra_data, dict):
            raise TypeError("extra_data must be a dictionary")


@dataclass
class Metadata:
    added: str = None

@dataclass
class Tag:
    id: str = None
    source: str = None

@dataclass
class ProfileItem:
    id: str
    objectId: str
    itemId: str
    objectSource: str
    itemSource: str
    metadata: Metadata
    additionalData: ItemAdditionalData
    tags: List[Tag]

@dataclass
class Avatar:
    gameId: str = None
    face: str = None
    full: str = None

@dataclass
class Node:
    id: str = None
    avatar: Avatar = field(default_factory=Avatar)

@dataclass
class FindProfilesResponse:
    totalCount: int = 0
    nodes: list[Node] = field(default_factory=list)

@dataclass
class ActorClothRel:
    ActorClothesRelId: int = 0
    ActorId: int = 0
    ClothesId: int = 0
    Color: str = None
    IsWearing: int = -1
    IsFav: int = -1
    AMF_CLASSNAME: str = "MovieStarPlanet.WebService.ActorClothes.AMFActorClothes.GetActorClothesRelMinimals"

    @classmethod
    def from_response_content(cls, **kwargs):
        return cls(**kwargs)
    
@dataclass
class Autograph:
    Fame: int = 0
    Timestamp: int = 0
    AMF_CLASSNAME = None

@dataclass
class Message:
    MessageId: str = None
    Version: int = 1
    ConversationId: str = 0
    MessageBody: str = None
    MessageType: str = None
    SenderProfileId: str = None
    Timestamp: int = 0
    AMF_CLASSNAME: str= "MovieStarPlanet.Model.Messages.ValueObjects.MessageV2"