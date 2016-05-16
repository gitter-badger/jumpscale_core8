import smtplib
from contextlib import contextmanager
from email.mime.text import MIMEText


class Sender:
    def __init__(self, username, password, host, port):
        self._host = host
        self._port = port
        self._username = username
        self._password = password

    @contextmanager
    def _connect(self):
        try:
            s = smtplib.SMTP(self._host, self._port)
            s.login(self._username, self._password)
            yield s
        finally:
            s.close()

    def send(self, to, from_, subject, content):
        msg = MIMEText(content)
        msg['Subject'] = subject
        if isinstance(to, str):
            msg['To'] = to
        else:
            msg['To'] = ', '.join(to)

        msg['From'] = from_
        with self._connect() as s:
            s.sendmail(from_, to, str(msg))
