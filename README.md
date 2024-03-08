An asynchronous library for seamless interaction with MovieStarPlanet's API.


# moviestarplanet
This is an asynchronous library designed to facilitate seamless interaction with the MovieStarPlanet API. Please note that while this library is not yet complete, it contains all the necessary components to exploit MovieStarPlanet. If you wish to run a few requests, you may need to add a websockets implementation.

# How to initialize the class
To begin using the MovieStarPlanet library, first, import the MovieStarPlanetAsync class and initialize it:
```python
import asyncio
from moviestarplanet import MovieStarPlanetAsync

async def main() -> None:
    moviestarplanet = MovieStarPlanetAsync()

asyncio.run(main=main())
```

# Example Usage
Once initialized, you can log in and use commands.
```python
import asyncio
from moviestarplanet import MovieStarPlanetAsync

async def main() -> None:
    moviestarplanet = MovieStarPlanetAsync()

    login = await moviestarplanet.login_async(username="user", password="password", server="fr", proxy=None)

    if login.loginStatus.isLoggedIn:
        success: bool = await moviestarplanet.claim_reward_async(award_type="VIP_STAR")
        blocked: bool = await moviestarplanet.block_user_async(3)

asyncio.run(main())
```

### here is the current list of all the functions:
`login_async(username, password, server, proxy=None)`
Login to MovieStarPlanet.

`claim_reward_async(award_type, proxy=None)`
Claim a reward.

`block_user_async(actorId, proxy=None)`
Block a user.

`get_piggy_bank_async(proxy=None)`
Retrieve piggy bank informations.

`search_actor_by_name_async(name, proxy=None)`
Retrieve a list of all the actors found.

# SoftUtils & BotUtils
The library also have cool things that can help you botting and doing soft rare on MovieStarPlanet2.
```python
from moviestarplanet import bot_utils
from moviestarplanet import soft_utilities

# Gets random credentials from a bot file in format: u:p:s if has_server = True else u:p
random_credentials = bot_utils.get_random_account_credentials('bots.txt', has_server=False)
print(random_credentials.username, random_credentials.password, random_credentials.server)

# That can help you for soft rare
soft = soft_utilities.SoftUtils(access_token=login.loginStatus.nebulaLoginStatus["accessToken"])
data = await soft.inventory_json_for_item_template_async(itemId=int(item_id))
data = soft.apply_color_to_item(data=data, colors=colors)
```
