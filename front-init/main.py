import datetime
import http.server
import json
import logging
import mimetypes
import pathlib
import socket
import threading
import urllib.parse
from http.server import HTTPServer


class HttpHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        data_dict = {key: value for key, value in [el.split('=') for el in post_data.split('&')]}
        self.socket_client_func(data_dict)

        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())

    def socket_client_func(self, data):
        host = 'localhost'
        port = 5000
        socket_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        data['datetime'] = str(datetime.datetime.now())
        socket_client.sendto(json.dumps(data).encode('utf-8'), (host, port))
        socket_client.close()


def socker_server_func():
    host = 'localhost'
    port = 5000

    socket_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_server.bind((host, port))

    try:
        while True:
            data, address = socket_server.recvfrom(1024)
            data = json.loads(data.decode('utf-8'))

            with open('storage/data.json', 'a') as f:
                json.dump({data['datetime']: {'username': data['username'], 'message': data['message']}}, f)
                f.write('\n')
    except Exception as err:
        logging.error(f'{err}')
    finally:
        socket_server.close()


def run(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ('0.0.0.0', 3000)
    http = server_class(server_address, handler_class)
    try:
        logging.debug('Started server')

        http_thread = threading.Thread(target=http.serve_forever)
        http_thread.start()

        socket_thread = threading.Thread(target=socker_server_func)
        socket_thread.start()

        http_thread.join()
        socket_thread.join()

    except KeyboardInterrupt:
        logging.debug('Shutting down')
        http.server_close()


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s %(message)s',
        level=logging.DEBUG,
        handlers=[
            logging.FileHandler("program.log"),
            logging.StreamHandler()
        ])
    run()