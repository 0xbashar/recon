import requests
import asyncio

class NotificationManager:
    def __init__(self, config):
        self.telegram_token = config.get('your token')
        self.telegram_chat_id = config.get('your id')
        self.slack_webhook = config.get('slack_webhook')
        self.generic_webhook = config.get('generic_webhook')

    def notify_finding(self, finding):
        # Send to all configured channels asynchronously
        asyncio.create_task(self._notify_all(finding))

    async def _notify_all(self, finding):
        msg = self._format_message(finding)
        if self.telegram_token:
            await self._send_telegram(msg)
        if self.slack_webhook:
            await self._send_slack(msg)
        if self.generic_webhook:
            await self._send_generic(finding)

    def _format_message(self, finding):
        return f"🚨 *New Finding*\nPlatform: {finding.get('platform', 'unknown')}\nURL: {finding['url']}\nType: {finding['type']}\nConfidence: {finding.get('confidence', 50)}%\nDetails: {finding.get('details', 'N/A')}"

    async def _send_telegram(self, message):
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        data = {'chat_id': self.telegram_chat_id, 'text': message, 'parse_mode': 'Markdown'}
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(url, json=data)
        except:
            pass

    async def _send_slack(self, message):
        if not self.slack_webhook:
            return
        data = {'text': message}
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(self.slack_webhook, json=data)
        except:
            pass

    async def _send_generic(self, finding):
        if not self.generic_webhook:
            return
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(self.generic_webhook, json=finding)
        except:
            pass
