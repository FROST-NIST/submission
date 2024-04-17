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

    def receive(self, size):
        self.download += size

    def send(self, size):
        self.upload += size
