class MLHeuristics:
    def __init__(self, enabled=True):
        self.enabled = enabled
        self.param_scores = {
            'id': 10,
            'file': 9,
            'redirect': 8,
            'url': 8,
            'page': 7,
            'user': 6,
            'admin': 6,
            'debug': 5,
            'test': 4
        }

    def score_parameter(self, param):
        if not self.enabled:
            return 5
        param_lower = param.lower()
        for key, score in self.param_scores.items():
            if key in param_lower:
                return score
        return 1

    def prioritize_endpoints(self, endpoints):
        """Return endpoints sorted by max parameter score."""
        scored = []
        for ep, params in endpoints.items():
            max_score = max((self.score_parameter(p) for p in params), default=0)
            scored.append((max_score, ep, params))
        scored.sort(reverse=True)
        return [(ep, params) for _, ep, params in scored]
