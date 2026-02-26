# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

import asyncio
import random
import json
import threading
import customtkinter as ctk
from lcu_driver import Connector


"""
######################
# RANDOM PICK LOGIC  #
######################
"""


async def pick_random_champion(connection):
    """
    Fetches the list of pickable champion IDs from the League Client
    and returns a randomly selected one.

    Args:
        connection: The active LCU connection object.

    Returns:
        int: A randomly chosen champion ID from the pickable pool.
    """
    ids = await connection.request('get', '/lol-champ-select/v1/pickable-champion-ids')
    pickable_champions = await ids.json()
    random_champion_id = random.choice(pickable_champions)
    print()
    print(f"Random: {random_champion_id}")
    return random_champion_id


async def session_id(connection):
    """
    Retrieves the current champion select session and determines
    the action ID associated with the local player's pick action.

    Args:
        connection: The active LCU connection object.

    Returns:
        int: The action ID of the local player's pick action, or -1 if not found.
    """
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
    """
    Sends a PATCH request to the LCU API to select a champion
    for the given pick action.

    Args:
        connection: The active LCU connection object.
        champ_id (int): The ID of the champion to select.
        pick_id (int): The action ID for the local player's pick slot.

    Note:
        Adding 'completed': True to the request data would also
        automatically lock in the champion selection.
    """
    patch = f"/lol-champ-select/v1/session/actions/{pick_id}"

    request = await connection.request('patch', patch, data={'championId': champ_id})
    if request.status == 204:
        print("Champion selected!")
    else:
        print(request.status)


async def pick_main_logic(connection):
    """
    Orchestrates the full random pick flow:
    picks a random champion, retrieves the session action ID,
    and submits the selection to the LCU API.

    Args:
        connection: The active LCU connection object.
    """
    id = await pick_random_champion(connection)
    pick_id = await session_id(connection)
    await select_random_champ(connection, id, pick_id)


"""
########################
# CONNECTOR & THREAD   #
########################
"""

# Create a dedicated event loop for the LCU connector and set it as the current loop.
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

cnct_on = None
connector = Connector(loop=loop)
keep_alive = asyncio.Event()

# Run the connector in a background daemon thread so it doesn't block the GUI.
t_connect = threading.Thread(target=connector.start, daemon=True)
t_connect.start()


def make_pick():
    """
    Schedules the pick_main_logic coroutine on the connector's event loop
    from the main (GUI) thread in a thread-safe manner.
    Does nothing if the client is not connected.
    """
    if cnct_on:
        asyncio.run_coroutine_threadsafe(pick_main_logic(cnct_on), connector.loop)
    else:
        print("Client not found")


@connector.ready
async def connect(connection):
    """
    Callback triggered when the LCU connector successfully establishes
    a connection to the League Client.

    Args:
        connection: The active LCU connection object.
    """
    global cnct_on
    cnct_on = connection
    print("Connected!")
    await keep_alive.wait()


@connector.close
async def disconnect(_):
    """
    Callback triggered when the LCU connector loses the connection
    to the League Client. Sets the keep_alive event to allow cleanup.
    """
    keep_alive.set()
    print("Disconnected")


"""
#############
#    GUI    #
#############
"""


def gui():
    """
    Builds and launches the CustomTkinter GUI window.
    Contains a single button that triggers the random champion pick flow.
    """
    app = ctk.CTk()
    app.geometry("300x150")
    app.title("Picker")
    app.columnconfigure(0, weight=1)

    button_pick = ctk.CTkButton(app, command=make_pick, text="Pick a champ")
    button_pick.grid(row=0, column=0, pady=20, padx=20, sticky="nsew")

    app.mainloop()


if __name__ == "__main__":
    gui()