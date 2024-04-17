# Communication traffic as seen by a specific participant.
class Traffic:
    def __init__(self):
        self.download = 0
        self.upload = 0

    def __repr__(self):
        return 'downloaded {} bytes, uploaded {} bytes'.format(
            self.download,
            self.upload,
        )

    def __add__(self, other):
        ret = Traffic()
        ret.download = self.download + other.download
        ret.upload = self.upload + other.upload
        return ret

    def receive(self, size):
        self.download += size

    def send(self, size):
        self.upload += size
