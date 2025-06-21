from queue import Queue, Empty
from threading import Thread, current_thread, Lock, Barrier
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import time
import random
from time import sleep
from random import randint

# Configure logging
from src.utils.filing_utils import get_logging_info
from opensourceleg.logging import Logger, LogLevel
CONSOLE_LOGGER = Logger(enable_csv_logging=False,
                        log_path=get_logging_info(user_input_flag=False)[0],
                        stream_level = LogLevel.INFO,
                        log_format = "%(levelname)s: %(message)s"
                        )

@dataclass()
class Mail:
    """
    Mail is a simple data structure that contains the sender and contents of a message.

    Args:
        sender (str): The name of the sending thread.
        contents (dict): The contents of the mail, typically a dictionary.
    """
    sender: str
    contents: Dict[str, Any]


class Inbox:
    """
    Inbox receives and stores mail for a given address (thread).
    The inbox belongs to this thread and is used to recieve messages directed to it.

    Args:
        address (str): The address of the inbox, typically the thread name.
    """
    def __init__(self, address: str) -> None:
        """
        Initialize a inbox with a given address.
        """
        self.address: str = address
        self._incoming_mail: Queue = Queue()

    def receive(self, mail: Mail) -> None:
        """
        Put mail in the inbox queue.
        Args:
            mail (Mail): The mail object to be received.
        """
        CONSOLE_LOGGER.info(f"      Mail put into {self.address} inbox: {mail}")
        self._incoming_mail.put_nowait(mail)

    def get_all_mail(self) -> List[Mail]:
        """
        Retrieve and remove all mail from the inbox queue.
        Returns:
            List[Mail]: All mail currently in the inbox.
        """

        mail: List[Mail] = []

        # retrive all mail from queue until empty
        # handles situation where data is continuously added to the queue
        while True:
            try:
                mail.append(self._incoming_mail.get_nowait())
            except Empty:
                break
        CONSOLE_LOGGER.info(f"All mail retrieved from {self.address}")
        return mail


class MessageRouter:
    """
    This class is used to coordinate inter-thread communication
    via queues. It's primary function is to send messages (mail) from one thread
    to another thread.

    One object should be created and shared between all threads.
    Each thread has its own inbox, and the MessageRouter acts as a central hub
    for sending and receiving messages between these inboxes.
    """
    def __init__(self) -> None:
        self._addressbook: Dict[str, Inbox] = {}
        self._lock = Lock() # lock to ensure thread-safe access to the addressbook

    def setup_addressbook(self, *threads: Thread) -> None:
        """
        Set up threads in the addressbook with corresponding inboxes.
        To access threads' inboxes, use the thread's `inbox` attribute.

        REMINDER: addressbook must be created prior to starting threads

        Args:
            *threads (Thread): Threads to register in the addressbook.
        """

        # to ensure that only one thread can access addressbook at a time
        with self._lock:
            for thread in threads:

                if hasattr(thread, 'inbox') and thread.inbox is not None:
                    # if thread already has a inbox, skip
                    CONSOLE_LOGGER.info(f"Inbox already exists for thread: {thread.name}")
                    continue

                elif not isinstance(thread, Thread):
                    # if thread is not a Thread instance, raise error
                    raise TypeError("Addressbook expected a Thread instance.")

                elif thread.name in self._addressbook:
                    # if thread name already exists in addressbook, skip
                    CONSOLE_LOGGER.warning(f"Thread name -- {thread.name} -- already exists in addressbook.")
                    continue

                elif not thread.name:
                    # if thread does not have a name, raise error
                    raise ValueError("Thread must have a name.")

                # instantiate a inbox for each thread
                inbox = Inbox(thread.name)
                thread.inbox = inbox

                # create dictionary mapping thread name to it's inbox
                self._addressbook[thread.name] = inbox
                CONSOLE_LOGGER.info(f"Inbox set up for thread: {thread.name}")

    def send(self, sender: str, recipient: str, contents: dict) -> None:
        """
        Send mail to a recipient's inbox.

        Args:
            sender (str): Name of the sender.
            recipient (str): Name of the recipient thread.
            contents (dict): The contents of the mail (must be a dictionary).
        Raises:
            KeyError: If the recipient does not exist in the addressbook.
        """

        # package mail into a Mail object
        mail = Mail(sender, contents)

        # to ensure that only one thread can access addressbook at a time
        with self._lock:
            # raise error if recipient is not in addressbook
            if recipient not in self._addressbook:
                raise KeyError(f"Recipient '{recipient}' not found in addressbook.")


            CONSOLE_LOGGER.info(f"{sender} sending to {recipient}")
            CONSOLE_LOGGER.info(f"      Message contents: {mail}")

            # send mail to recipient's inbox
            self._addressbook[recipient].receive(mail)


def f(msg_router, barrier):
    """
    This target function sends random amount of mail and counts amount of mail received at 1Hz.
    Waits at the barrier until all threads are ready before sending mail.
    """
    which = current_thread()
    which.msg_count = 0
    CONSOLE_LOGGER.info("Started " + which.name)

    # Wait for all threads to be ready before sending mail
    barrier.wait()

    while True:
        # Random delay before sending mail to increase race condition likelihood
        sleep(random.uniform(0, 0.05))

        for _ in range(randint(2, 5)):
            try:
                random_recipient = "thread" + str(randint(1, barrier.parties))

                # ensure that the recipient is not the same as the sender
                if random_recipient == which.name:
                    continue

                # Create a unique message with a timestamp and message ID
                elapsed = time.time() - START_TIME
                unique_msg = {
                    "message": f"sending...",
                    "timestamp": f"{elapsed:0.2}",
                    "msg_id": f"{which.name}_{random_recipient}"
                }

                # Random delay before sending
                sleep(random.uniform(0, 0.02))

                # send the mail to the thread's inbox
                msg_router.send(which.name, random_recipient, unique_msg)
            except Exception as e:
                CONSOLE_LOGGER.error(f"{which.name} failed to send to {random_recipient}: {e}")
                pass

        # After sending mail, it retrieves all mail from the current thread's inbox
        mymail = which.inbox.get_all_mail()
        for mail in mymail:
            CONSOLE_LOGGER.info(f"unpacking {which.name} inbox")
            CONSOLE_LOGGER.info(f"      {mail.sender} had sent this: {mail.contents}")
        which.msg_count += len(mymail)

        CONSOLE_LOGGER.info(f"\n")
        sleep(1.0)



START_TIME = time.time()

if __name__ == "__main__":

    # Create PostOffice with empty addressbook
    msg_router = MessageRouter()

    # Set the number of threads
    num_threads = 3

    # Create threads with unique names
    thread_names = [f"thread{i+1}" for i in range(num_threads)]
    threads = []
    for name in thread_names:
        threads.append(Thread(target=f, args=(msg_router, None), daemon=True, name=name))

    # Create a barrier for all threads
    barrier = Barrier(num_threads)

    # Assign the barrier to each thread's args
    for thread in threads:
        thread._args = (msg_router, barrier)

    # Populate addressbook with threads
    msg_router.setup_addressbook(*threads)

    # Start all threads
    for thread in threads:
        thread.start()

    # Print out mail flow summary every 0.5 Hz (slower than threads)
    while True:
        try:
            CONSOLE_LOGGER.info("\nMessage Summary\n")
            for thread in threads:
                CONSOLE_LOGGER.info(f"{thread.name}, msg count: {thread.msg_count}, time: {time.time() - START_TIME:0.2f} seconds")
                thread.msg_count = 0
            sleep(2.0)

        except KeyboardInterrupt:
            CONSOLE_LOGGER.info("Shutting down mail summary loop.")
            break
