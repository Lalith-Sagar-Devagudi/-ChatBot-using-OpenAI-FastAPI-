import subprocess
import http.server
import socketserver
import webbrowser
import threading
import signal
import sys

PORT = 8001
HTML_FILE = "cbtbox.html"

# Start the FastAPI server in a separate thread
def start_fastapi_server():
    subprocess.run(["uvicorn", "microservice:app", "--reload"])

# Open the HTML file in the browser
def open_html_file():
    webbrowser.open_new_tab(f"http://localhost:{PORT}/{HTML_FILE}")

# Start the HTTP server to serve the HTML file
def start_http_server():
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving at http://localhost:{PORT}/{HTML_FILE}")
        open_html_file()  # Call to open the HTML file
        httpd.serve_forever()


# Signal handler to capture the interrupt signal (CTRL+C)
def signal_handler(sig, frame):
    print("\nShutting down servers...")
    sys.exit(0)

# Prompt the user for confirmation to stop the servers
def prompt_confirmation():
    confirmation = input("Do you want to stop the servers? (y/n): ")
    if confirmation.lower() == "y":
        print("Shutting down servers...")
        sys.exit(0)


# Start both servers in separate threads
fastapi_thread = threading.Thread(target=start_fastapi_server)
http_thread = threading.Thread(target=start_http_server)

fastapi_thread.start()
http_thread.start()

# Register the signal handler for interrupt signal (CTRL+C)
signal.signal(signal.SIGINT, signal_handler)

# Prompt for user confirmation before exiting
while True:
    prompt_confirmation()

# # Wait for both threads to finish
# fastapi_thread.join()
# http_thread.join()
