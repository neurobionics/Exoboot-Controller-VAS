from queue import Queue, Empty
from threading import Thread, current_thread, Lock, Barrier
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
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
    Represents a mail message with a sender and contents.
    """
    sender: str
    contents: Any

class MailBox:
    """
    MailBox receives and stores mail for a given address (thread).
    The mailbox belongs to this thread and is used to recieve messages directed to it.

    Args:
        address (str): The address of the mailbox, typically the thread name.
    """
    def __init__(self, address: str) -> None:
        """
        Initialize a MailBox with a given address.
        """
        self.address: str = address
        self._incoming_mail: Queue = Queue()

    def receive(self, mail: Mail) -> None:
        """
        Put mail in the mailbox queue.
        Args:
            mail (Mail): The mail object to be received.
        """
        CONSOLE_LOGGER.info(f"Mail received at {self.address}: {mail}")
        self._incoming_mail.put_nowait(mail)

    def getmail_all(self) -> List[Mail]:
        """
        Retrieve and remove all mail from the mailbox queue.
        Returns:
            List[Mail]: All mail currently in the mailbox.
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

class PostOffice:
    """
    This PostOffice class is used to coordinate inter-thread communication
    via queues. It's primary function is to send messages (mail) from one thread
    to another thread.

    One PostOffice should be created and shared between all threads.
    Each thread has its own mailbox, and the postoffice acts as a central hub
    for sending and receiving messages between these mailboxes.
    """
    def __init__(self) -> None:
        self._addressbook: Dict[str, MailBox] = {}
        self._lock = Lock() # lock to ensure thread-safe access to the addressbook

    def setup_addressbook(self, *threads: Thread) -> None:
        """
        Set up threads in the addressbook with corresponding mailboxes.
        To access threads' mailboxes, use the thread's `mailbox` attribute.
        Args:
            *threads (Thread): Threads to register in the addressbook.
        """

        with self._lock:
            for thread in threads:

                if hasattr(thread, 'mailbox') and thread.mailbox is not None:
                    # if thread already has a mailbox, skip
                    CONSOLE_LOGGER.info(f"Mailbox already exists for thread: {thread.name}")
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

                # instantiate a mailbox for each thread
                mailbox = MailBox(thread.name)
                thread.mailbox = mailbox

                # create dictionary mapping thread name to it's mailbox
                self._addressbook[thread.name] = mailbox
                CONSOLE_LOGGER.info(f"Mailbox set up for thread: {thread.name}")

    def send(self, sender: str, recipient: str, contents: Any) -> None:
        """
        Send mail to a recipient's mailbox.

        Args:
            sender (str): Name of the sender.
            recipient (str): Name of the recipient thread.
            contents (Any): The contents of the mail.
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

            self._addressbook[recipient].receive(mail)
            CONSOLE_LOGGER.info(f"Mail sent from {sender} to {recipient}: {mail.contents}")

def f(postoffice, barrier):
    """
    Target function sends random amount of mail and counts amount of mail received at 1Hz.
    Waits at the barrier until all threads are ready before sending mail.
    """
    which = current_thread()
    which.mailcount = 0
    CONSOLE_LOGGER.info("Started " + which.name)

    # Wait for all threads to be ready before sending mail
    barrier.wait()

    while True:
        # Send a random amount of mail to other addresses in the postoffice addressbook
        for _ in range(randint(2, 5)):
            try:
                random_recipient = "thread" + str(randint(1, 3))

                # ensure that the recipient is not the same as the sender
                if random_recipient == which.name:
                    continue

                postoffice.send(which.name, random_recipient, f"Hi from {which.name} to {random_recipient}!")
            except:
                pass

        # Get mail and add to mailcount
        mymail = which.mailbox.getmail_all()
        which.mailcount += len(mymail)

        sleep(1.0)

if __name__ == "__main__":

    # Create PostOffice with empty addressbook
    postoffice = PostOffice()

    # Set the number of threads
    num_threads = 3

    # Create threads with unique names
    thread_names = [f"thread{i+1}" for i in range(num_threads)]
    threads = []
    for name in thread_names:
        threads.append(Thread(target=f, args=(postoffice, None), daemon=True, name=name))

    # Create a barrier for all threads
    barrier = Barrier(num_threads)

    # Assign the barrier to each thread's args
    for thread in threads:
        thread._args = (postoffice, barrier)

    # Populate addressbook with threads
    postoffice.setup_addressbook(*threads)

    # Start all threads
    for thread in threads:
        thread.start()

    # Print out mailflow summary every 2 seconds
    while True:
        try:
            CONSOLE_LOGGER.info("\nMail Summary\n")
            for thread in threads:
                CONSOLE_LOGGER.info(f"{thread.name} {thread.mailcount}")
                thread.mailcount = 0
            sleep(2.0)

        except KeyboardInterrupt:
            CONSOLE_LOGGER.info("Shutting down mail summary loop.")
            break
