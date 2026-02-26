# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

import asyncio
import random 
import json
import threading
import customtkinter as ctk
from lcu_driver import Connector



"""
######################
# LOGICA RANDOM PICK #
######################
"""

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
    
    request = await connection.request('patch', patch, data = {'championId': champ_id}) # posso far confermare automaticamente le cose aggiungendo 'completed': True
    if request.status == 204:
        print("champ selected!")
        
    else:
        print(request.status)
    

async def pick_logic(connection):
    id = await pick_random_champion(connection)
    pick_id = await session_id(connection)
    await select_random_champ(connection, id, pick_id)

"""
#############
# CONNECTOR & THREAD #
#############
"""

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

cnct_on = None
connector = Connector(loop=loop)
keep_alive = asyncio.Event()

t_connect = threading.Thread(target= connector.start, daemon=True)
t_connect.start()

def make_pick():
    if cnct_on:
        asyncio.run_coroutine_threadsafe(pick_logic(cnct_on), connector.loop)
    else:
        print("Client not found")

@connector.ready
async def connect(connection):
    global cnct_on
    cnct_on = connection
    print("Connected!")
    await keep_alive.wait()

@connector.close
async def disconnect(_):
    keep_alive.set()
    print("Disconnected")





"""
#############
# PARTE GUI #
#############
"""
def gui():
    app = ctk.CTk()
    app.geometry("300x150")
    app.title("Picker")
    app.columnconfigure(0, weight=1)

    button_pick = ctk.CTkButton(app, command=make_pick, text= "Pick a champ", )
    button_pick.grid(row = 0, column=0, pady = 20, padx = 20 ,sticky = "nsew")

    app.mainloop()


if __name__ == "__main__":
    gui()




