import pytest
from exoboot_messenger_hub import Mail, MailBox, PostOffice

class DummyThread:
    def __init__(self, name: str):
        self.name: str = name
        self.mailbox: MailBox | None = None

def test_mail_function() -> None:
    """
    Test the Mail function.
    Verifies that Mail returns a dictionary with the correct sender and contents.
    """
    mail = Mail('sender1', 'hello')
    assert mail == {'sender': 'sender1', 'contents': 'hello'}

def test_mailbox_receive_and_getmail_all() -> None:
    """
    Test MailBox.receive and MailBox.getmail_all.
    Ensures that received mail is stored and getmail_all returns all mail, then empties the mailbox.
    """
    mailbox = MailBox('address1')
    mail1 = Mail('sender1', 'msg1')
    mail2 = Mail('sender2', 'msg2')
    mailbox.receive(mail1)
    mailbox.receive(mail2)
    all_mail = mailbox.getmail_all()
    assert mail1 in all_mail
    assert mail2 in all_mail
    assert mailbox.getmail_all() == []  # Should be empty after reading

def test_postoffice_send_and_setup_addressbook() -> None:
    """
    Test PostOffice.setup_addressbook and PostOffice.send.
    Checks that threads are added to the addressbook and mail is delivered to the correct mailbox.
    """
    postoffice = PostOffice()
    t1 = DummyThread('thread1')
    t2 = DummyThread('thread2')
    postoffice.setup_addressbook(t1, t2)
    assert 'thread1' in postoffice.addressbook
    assert 'thread2' in postoffice.addressbook
    postoffice.send('thread1', 'thread2', 'test-message')
    received = t2.mailbox.getmail_all()
    assert received[0]['sender'] == 'thread1'
    assert received[0]['contents'] == 'test-message'
    assert t2.mailbox.getmail_all() == []

def test_postoffice_send_to_nonexistent() -> None:
    """
    Test PostOffice.send error handling.
    Ensures that sending mail to a nonexistent recipient raises a KeyError.
    """
    postoffice = PostOffice()
    t1 = DummyThread('thread1')
    postoffice.setup_addressbook(t1)
    with pytest.raises(KeyError):
        postoffice.send('thread1', 'threadX', 'fail')
