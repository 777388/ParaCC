import json
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import requests
import asyncio
import aiohttp
import concurrent.futures
import urllib.parse

class RequestHandler(BaseHTTPRequestHandler):
    async def _search_commoncrawl(self, domain, query):
        try:
            url = f'http://index.commoncrawl.org/CC-MAIN-2021-22-index?url={domain}&output=json'
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    data = await resp.json()
            matches = []
            async def search_url(record):
                url = record['url']
                if query in url:
                    matches.append(url)
            with concurrent.futures.ProcessPoolExecutor() as executor:
                loop = asyncio.get_event_loop()
                tasks = [loop.run_in_executor(executor, search_url, record) for record in data['records']]
                await asyncio.gather(*tasks)
            return matches
        except Exception as e:
            print(e)
            return "Error searching Common Crawl"

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed_path.query)
        if 'domain' in params and 'query' in params:
            domain = params['domain'][0]
            query = params['query'][0]
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            matches = loop.run_until_complete(self._search_commoncrawl(domain, query))
            if matches:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write("<h1>Matching URLs:</h1>")
                for url in matches:
                    self.wfile.write("<p>" + url + "</p>")
            else:
                self.send_response(204)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write("<h1>No matching URLs found</h1>")
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write("<h1>Invalid Request</h1>")

def run(server_class=HTTPServer, handler_class=RequestHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print('Starting server on port {}...'.format(port))
    httpd.serve_forever()

run()
