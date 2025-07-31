class job:
    def __init__(self, title: str, company: str = "", job_url: str = "", description: str = "", location: str = "", is_remote: bool = False, score: int = 0, recommendations: str = "", curated: bool = False, curated_resume: str = ""):
        self.title = title
        self.company = company
        self.job_url = job_url
        self.description = description
        self.location = location
        self.is_remote = is_remote
        self.score = score
        self.recommendations = recommendations
        self.curated = curated
        self.curated_resume = curated_resume

class job_comparisons:
    def __init__(self, job_url: str = "", score: int = 0, content: str = ""):
        self.job_url = job_url
        self.score = score
        self.content = content