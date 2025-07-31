class jobs:
    def __init__(self, title: str, company: str = "", job_url: str = "", description: str = "", location: str = "", is_remote: bool = False, score: int = 0):
        self.title = title
        self.company = company
        self.job_url = job_url
        self.description = description
        self.location = location
        self.is_remote = is_remote
        self.score = score

class job_comparisons:
    def __init__(self, job_url: str = "", score: int = 0, content: str = ""):
        self.job_url = job_url
        self.score = score
        self.content = content