import re
from collections import defaultdict

class AnomalyDetector:
    def __init__(self, config):
        self.config = config
        self.baselines = {}  # key: endpoint+method+params
        self.threshold = config.get('length_threshold', 0.2)
        self.keyword_patterns = config.get('keyword_patterns', [])

    def record_baseline(self, url, method, params, response, body):
        key = self._key(url, method, params)
        self.baselines[key] = {
            'status': response.status,
            'length': len(body),
            'headers': dict(response.headers),
            'keywords': self._extract_keywords(body)
        }

    def detect(self, url, method, params, response, body):
        key = self._key(url, method, params)
        if key not in self.baselines:
            return False, "No baseline"
        base = self.baselines[key]
        anomalies = []
        if response.status != base['status']:
            anomalies.append(f"Status {base['status']} -> {response.status}")
        length_change = abs(len(body) - base['length']) / base['length'] if base['length'] else 0
        if length_change > self.threshold:
            anomalies.append(f"Length {base['length']} -> {len(body)} ({length_change*100:.1f}% change)")
        new_keywords = self._extract_keywords(body) - base['keywords']
        if new_keywords:
            anomalies.append(f"New keywords: {new_keywords}")
        return len(anomalies) > 0, anomalies

    def _key(self, url, method, params):
        # Simplified: use URL without query as key (ignoring params)
        return url.split('?')[0] + '|' + method

    def _extract_keywords(self, text):
        keywords = set()
        for pattern in self.keyword_patterns:
            if re.search(pattern, text, re.I):
                keywords.add(pattern)
        return keywords
