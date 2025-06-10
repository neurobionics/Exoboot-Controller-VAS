from queue import Queue, Empty
from threading import Thread, current_thread


def Mail(sender, contents):
    return {"sender": sender, "contents": contents}
        

class MailBox:
    def __init__(self, address):
        self.address = address
        self.incoming_mail = Queue()

    def receive(self, mail):
        self.incoming_mail.put_nowait(mail)

    def getmail_all(self):
        mail = []
        while True:
            try:
                mail.append(self.incoming_mail.get_nowait())
            except Empty:
                break

        return mail
    

class PostOffice:
    def __init__(self, *threads):
        self.addressbook = {}
        # self._setup_addressbook(*threads)

    def _setup_addressbook(self, *threads):
        for thread in threads:
            mailbox = MailBox(thread.name)
            thread.mailbox = mailbox
            self.addressbook[thread.name] = mailbox

    def send(self, sender, recipient, contents):
        mail = Mail(sender, contents)
        self.addressbook[recipient].receive(mail)


if __name__ == "__main__":
    from time import sleep
    from random import randint

    def f(postoffice):
        which = current_thread()
        which.mailcount = 0
        print("Started ", which.name)
        while True:
            for _ in range(randint(2, 5)):
                try:
                    random_recipient = "thread" + str(randint(1, 3))
                    postoffice.send(which.name, random_recipient, f"Hi from {which}")
                except:
                    pass

            mymail = which.mailbox.getmail_all()
            
            which.mailcount += len(mymail)
            
            sleep(1.0)
    
    postoffice = PostOffice()

    thread1 = Thread(target=f, args=(postoffice,), daemon=True, name="thread1")
    thread2 = Thread(target=f, args=(postoffice,), daemon=True, name="thread2")
    thread3 = Thread(target=f, args=(postoffice,), daemon=True, name="thread3")

    postoffice._setup_addressbook(thread1, thread2, thread3)

    thread1.start()
    thread2.start()
    thread3.start()

    while True:
        try:
            print("\nMail Summary")
            for thread in [thread1, thread2, thread3]:
                print(thread.name, thread.mailcount)
                thread.mailcount = 0
            sleep(2.0)
        except KeyboardInterrupt:
            break
