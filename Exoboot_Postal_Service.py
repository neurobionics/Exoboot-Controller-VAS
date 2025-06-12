from queue import Queue, Empty
from threading import Thread, current_thread


def Mail(sender, contents):
    return {"sender": sender, "contents": contents}
        

class MailBox:
    """
    TBD Description

    Receive mail from other addresses
    """
    def __init__(self, address):
        self.address = address
        self.incoming_mail = Queue()

    def receive(self, mail):
        """
        Put mail in queue
        """
        self.incoming_mail.put_nowait(mail)

    def getmail_all(self):
        """
        Return all mail in queue
        """
        mail = []
        while True:
            try:
                mail.append(self.incoming_mail.get_nowait())
            except Empty:
                break

        return mail
    

class PostOffice:
    """
    TBD Description

    Send mail to other addresses(threads)
    """
    def __init__(self):
        self.addressbook = {}

    def setup_addressbook(self, *threads):
        """
        Set up thread in addressbook with a corresponding mailbox
        """
        for thread in threads:
            mailbox = MailBox(thread.name)
            thread.mailbox = mailbox
            self.addressbook[thread.name] = mailbox

    def send(self, sender, recipient, contents):
        """
        Send mail to recipient
        Mail needs to have a sender and contents to be complete
        """
        mail = Mail(sender, contents)
        self.addressbook[recipient].receive(mail)


if __name__ == "__main__":
    from time import sleep
    from random import randint

    def f(postoffice):
        """
        Target function sends random amount of mail and counts amount of mail received at 1Hz
        """
        which = current_thread()
        which.mailcount = 0

        print("Started ", which.name)
        while True:
            # Send a random amount of mail to other addresses in the postoffice addressbook
            for _ in range(randint(2, 5)):
                try:
                    random_recipient = "thread" + str(randint(1, 3))
                    postoffice.send(which.name, random_recipient, f"Hi from {which}")
                except:
                    pass

            # Get mail and add to mailcount
            mymail = which.mailbox.getmail_all()
            which.mailcount += len(mymail)
            
            sleep(1.0)
    
    # Create PostOffice with empty addressbook
    postoffice = PostOffice()

    # Create threads
    thread1 = Thread(target=f, args=(postoffice,), daemon=True, name="thread1")
    thread2 = Thread(target=f, args=(postoffice,), daemon=True, name="thread2")
    thread3 = Thread(target=f, args=(postoffice,), daemon=True, name="thread3")

    # Populate addressbook with threads
    postoffice.setup_addressbook(thread1, thread2, thread3)

    # Start threads
    thread1.start()
    thread2.start()
    thread3.start()

    # Print out mailflow summary every 2 seconds
    while True:
        try:
            print("\nMail Summary")
            for thread in [thread1, thread2, thread3]:
                print(thread.name, thread.mailcount)
                thread.mailcount = 0
            sleep(2.0)
        except KeyboardInterrupt:
            break
