import cv2
from flask import Flask, Response
import threading
import time

app = Flask(__name__)

class RTSPStreamer:
    def __init__(self):
        self.streams = {}
        self.locks = {}
    
    def get_stream(self, rtsp_url):
        if rtsp_url not in self.streams:
            self.streams[rtsp_url] = None
            self.locks[rtsp_url] = threading.Lock()
            threading.Thread(target=self._capture_stream, args=(rtsp_url,), daemon=True).start()
        return self.streams[rtsp_url]
    
    def _capture_stream(self, rtsp_url):
        cap = cv2.VideoCapture(rtsp_url)
        while True:
            ret, frame = cap.read()
            if ret:
                with self.locks[rtsp_url]:
                    self.streams[rtsp_url] = frame
            time.sleep(0.033)  # ~30 FPS

streamer = RTSPStreamer()

@app.route('/stream/<path:rtsp_url>')
def stream_rtsp(rtsp_url):
    def generate():
        while True:
            frame = streamer.get_stream(rtsp_url)
            if frame is not None:
                _, buffer = cv2.imencode('.jpg', frame)
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            time.sleep(0.033)
    
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8889, debug=False)