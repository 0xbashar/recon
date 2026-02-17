from urllib.parse import urlparse, parse_qs
import re

class ParamExtractor:
    def __init__(self, urls, scope_regex=None):
        self.urls = urls
        self.scope_regex = scope_regex
        self.junk_params = {'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content', 'fbclid', 'gclid', '_ga', '_gl', 'mc_cid', 'mc_eid', '_bta_tid', '_bta_c', 'trk', 'trkCampaign', 'trkContent', 'trkInfo', 'trkPage', 'trkModule', 'trkModulePosition', 'trkReferer', 'trkSource', 'trkCampaignId', 'trkContentId', 'trkInfoId', 'trkModuleId', 'trkModulePositionId', 'trkRefererId', 'trkSourceId'}

    def extract(self):
        endpoints = {}
        for url in self.urls:
            if self.scope_regex and not re.match(self.scope_regex, url):
                continue
            parsed = urlparse(url)
            query = parse_qs(parsed.query)
            path = parsed.scheme + "://" + parsed.netloc + parsed.path
            solid_params = []
            for param, values in query.items():
                if param.lower() in self.junk_params:
                    continue
                # Keep params that look interesting
                if self._is_interesting_param(param, values):
                    solid_params.append(param)
            if solid_params:
                if path not in endpoints:
                    endpoints[path] = set()
                endpoints[path].update(solid_params)
        # Convert sets to lists
        for path in endpoints:
            endpoints[path] = list(endpoints[path])
        return endpoints

    def _is_interesting_param(self, param, values):
        # Heuristics: check name and values
        interesting_keywords = ['id', 'file', 'redirect', 'url', 'page', 'path', 'doc', 'view', 'dir', 'show', 'cat', 'action', 'mode', 'type', 'name', 'user', 'profile', 'order', 'sort', 'filter', 'search', 'query', 'return', 'next', 'prev', 'refer', 'callback', 'data', 'json', 'xml', 'template', 'include', 'load', 'read', 'import', 'export', 'download', 'upload', 'img', 'image', 'icon', 'avatar', 'profile_pic', 'photo', 'picture', 'file_name', 'file_path']
        if any(k in param.lower() for k in interesting_keywords):
            return True
        # If value looks like a number or path, might be interesting
        for v in values:
            if v.isdigit() or v.startswith('/') or '.' in v:
                return True
        return False
