import http.server
import socketserver
import os
import json
import urllib.parse
import signal
import sys

PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
MUSIC_DIR = os.path.join(DIRECTORY, 'music')

# S'assurer que le dossier music existe
if not os.path.exists(MUSIC_DIR):
    os.makedirs(MUSIC_DIR)
    print(f"📁 Dossier 'music' créé à: {MUSIC_DIR}")

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # On ne sert plus de fichiers statiques depuis Python, Caddy s'en charge
        super().__init__(*args, directory="/tmp", **kwargs)

    # Gérer les requêtes OPTIONS pour le CORS (important pour les appels fetch modernes)
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        
        if parsed_path.path in ['/api/tracks', '/api/tracks/']:
            try:
                # --- CORRECTION CRUCIALE ---
                # L'ordre d'envoi de la réponse HTTP est maintenant correct :
                # 1. Statut, 2. En-têtes, 3. Fin des en-têtes, 4. Corps de la réponse.
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', '*')
                self.end_headers()
                
                if not os.path.exists(MUSIC_DIR):
                    self.wfile.write(json.dumps([]).encode())
                    return
                    
                files = sorted([f for f in os.listdir(MUSIC_DIR) if f.lower().endswith('.mp3')])
                
                playlist = []
                for filename in files:
                    # Construit l'URL que le navigateur utilisera pour accéder au fichier
                    # Caddy interceptera cette URL et servira le fichier
                    file_url = f"/music/Beats/music/{urllib.parse.quote(filename)}"
                    playlist.append({
                        "title": filename.replace('.mp3', ''),
                        "file": file_url
                    })
                
                self.wfile.write(json.dumps(playlist).encode())
                print(f"🎵 {len(playlist)} pistes envoyées avec URLs")
            except Exception as e:
                print(f"❌ Erreur API tracks: {e}")
                self.send_error(500, f"Could not list tracks: {e}")
        else:
            # Si la route n'est pas l'API, on retourne une erreur 404
            self.send_error(404, "Not Found: API endpoint not found")

    def log_message(self, format, *args):
        # Personnaliser les logs
        print(f"🌐 {self.address_string()} - {format % args}")

def signal_handler(signum, frame):
    print(f'\n🛑 Signal {signum} reçu, arrêt du serveur.')
    sys.exit(0)

def start_server():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    with socketserver.ThreadingTCPServer(("127.0.0.1", PORT), Handler) as httpd:
        httpd.allow_reuse_address = True
        print(f"🚀 Serveur API GLEAPHE démarré sur http://127.0.0.1:{PORT}")
        print(f"📁 Répertoire: {DIRECTORY}")
        print(f"🎵 Dossier musique: {MUSIC_DIR}")
        print("⚙️  Ce serveur ne fournit que l'API. Caddy gère les fichiers statiques.")
        print("Appuyez sur Ctrl+C pour arrêter le serveur.")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Arrêt du serveur (KeyboardInterrupt).")
        finally:
            httpd.shutdown()

if __name__ == "__main__":
    start_server()
