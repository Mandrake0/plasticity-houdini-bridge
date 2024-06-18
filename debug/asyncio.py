"""
asyncio new event Loop works when it is done inside a thread.  
on the main thread it gets the Houdini asyncio event loop that can't be used.

test script used in Windows -> Python Source Editor (hou.session)
Python Console: hou.session.run()
"""

import asyncio
import threading
import hou

# custom coroutine
async def main():
    # report a message
    print('main coroutine started')
    await asyncio.sleep(2)
    hou.session.test = "YES"
    print('it works')

def run_event_loop(txt):
    # start the event loop
    loop = asyncio.new_event_loop()
    print(loop)
    print(txt)
    loop.run_until_complete(main())
    
# start the asyncio program
def run():
    # create a new thread to execute a target coroutine
    thread = threading.Thread(target=run_event_loop, args=("Hello",))
    # start the new thread
    thread.start()
    
    