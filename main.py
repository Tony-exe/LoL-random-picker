# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

import asyncio
import random 
import json
from lcu_driver import Connector

# Crea un nuovo event loop manualmente e impostalo come predefinito
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Passa il loop che hai appena creato al Connector
connector = Connector(loop=loop)

# Generate a random champion ID
async def pick_random_champion(connection):
    ids = await connection.request('get', '/lol-champ-select/v1/pickable-champion-ids')
    pickable_champions = await ids.json()
    random_champion_id = random.choice(pickable_champions)
    print()
    print(f"Random: {random_champion_id}")
    return random_champion_id


async def session_id(connection):
    request = await connection.request('get', '/lol-champ-select/v1/session')
    session = await request.json()
    localCell: int = session['localPlayerCellId']
    pick: int = 1
    session_id: int = -1
    print(f"Cell: {localCell}")
    if session['actions'][0][0]['type'] == "pick":
        pick = 0
    for action in session['actions'][pick]:
        if action['actorCellId'] == localCell:
            session_id = action['id']
            print(f"Pick id: {session_id}")

    return session_id
        
async def select_random_champ(connection, champ_id, pick_id):
    patch = f"/lol-champ-select/v1/session/actions/{pick_id}"
    complete = f"{patch}/complete"
    request = await connection.request('patch', patch, data = {'championId': champ_id}) # posso far confermare automaticamente le cose aggiungendo 'completed': True
    final = await connection.request('post', complete) #Da vedere perché non va
    if request.status == 204:
        print("champ selected!")
        
    else:
        print(request.status)
   


@connector.ready
async def connect(connection):
    id = await pick_random_champion(connection)
    pick_id = await session_id(connection)
    await select_random_champ(connection, id, pick_id)

@connector.close
async def disconnect(_):
    print('End')

# Avvia il connector
connector.start()

