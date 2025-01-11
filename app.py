import os
import spotipy
from flask import Flask, redirect, request, session, url_for, render_template
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

sp_oauth = SpotifyOAuth(client_id=os.getenv('SPOTIPY_CLIENT_ID'),
                        client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'),
                        redirect_uri=os.getenv('SPOTIPY_REDIRECT_URI'),
                        scope="user-library-read user-read-playback-state user-modify-playback-state")

@app.route('/')
def index():
    if 'token_info' in session:
        return render_template('index.html', token=True)
    else:
        return render_template('index.html', token=False)

@app.route('/login')
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['token_info'] = token_info
    return redirect(url_for('index'))

@app.route('/search', methods=['POST'])
def search():
    token_info = get_token()
    sp = spotipy.Spotify(auth=token_info['access_token'])
    
    genre = request.form['genre']
    min_bpm = float(request.form['min_bpm'])
    max_bpm = float(request.form['max_bpm'])
    
    results = sp.search(q=f'genre:{genre}', type='track', limit=50)
    
    filtered_tracks = []
    
    for track in results['tracks']['items']:
        try:
            audio_features = sp.audio_features([track['id']])[0]
            bpm = audio_features['tempo']
            
            if min_bpm <= bpm <= max_bpm:
                filtered_tracks.append(track['name'])
        except Exception as e:
            print(f"Error in processing track {track['name']}: {e}")
    
    return render_template('index.html', token=True, tracks=filtered_tracks)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

def get_token():
    token_info = session.get('token_info', None)
    if not token_info:
        raise Exception("No token_info")
    
    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 60

    if is_expired:
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
    
    return token_info

if __name__ == '__main__':
    app.run(debug=True)
