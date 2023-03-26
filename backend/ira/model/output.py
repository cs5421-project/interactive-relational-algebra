from typing import Optional

from ira.model.query import Query


class Output:
    def __init__(self, status_code, query: Optional[Query], result=None, message=""):
        if result is None:
            result = dict()
        self.status_code = status_code
        self.message = message
        self.result = result
        self.value = {"sqlQuery": getattr(query,'value',''),
                      "message": message,
                      "result": result}

