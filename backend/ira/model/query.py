class Query:
    def __init__(self, value):
        self.value = value
        self.is_dql = self.is_dql()

    def is_dql(self):
        # TODO
        return True
