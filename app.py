import os
import spotipy
from flask import Flask, redirect, request, session, url_for, render_template
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import time

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Spotify credentials and redirect URI
sp_oauth = SpotifyOAuth(client_id='faebce212cb24ebeab3e4b8e58293ba2',
                        client_secret='8bdaddb842684d1db653b0d30b28057e',
                        redirect_uri='http://localhost:5000/callback',
                        scope="user-library-read user-read-playback-state user-modify-playback-state user-read-private")

@app.route('/')
def index():
    if 'token_info' in session:
        print(f"Token Info in Session: {session['token_info']}")  # Debug statement
        return render_template('index.html', token=True)
    else:
        print("No token_info in session")  # Debug statement
        return render_template('index.html', token=False)

@app.route('/login')
def login():
    auth_url = sp_oauth.get_authorize_url()
    print(f"Authorization URL: {auth_url}")  # Debug statement
    return redirect(auth_url)

@app.route('/callback')
def callback():
    session.clear()
    code = request.args.get('code')
    print(f"Authorization Code: {code}")  # Debug statement
    token_info = sp_oauth.get_access_token(code)
    
    # Debug statements
    print(f"Token Info Retrieved: {token_info}")
    
    if token_info:
        session['token_info'] = token_info
        print("Token Info Stored in Session")
    else:
        print("Failed to Retrieve Token Info")
    
    return redirect(url_for('index'))

@app.route('/search', methods=['POST'])
def search():
    try:
        token_info = get_token()
        sp = spotipy.Spotify(auth=token_info['access_token'])

        genre = request.form['genre']
        min_bpm = float(request.form['min_bpm'])
        max_bpm = float(request.form['max_bpm'])

        results = sp.search(q=f'genre:{genre}', type='track', limit=50)
        filtered_tracks = []

        for track in results['tracks']['items']:
            try:
                # Fetch audio features for each track
                audio_features = sp.audio_features([track['id']])
                if audio_features:
                    bpm = audio_features[0]['tempo']

                    if min_bpm <= bpm <= max_bpm:
                        filtered_tracks.append(track['name'])
            except spotipy.exceptions.SpotifyException as e:
                print(f"Error in processing track {track['name']}: {e}")
                print(f"HTTP Error details: status - {e.http_status}, reason - {e.reason}")
            except Exception as ex:
                print(f"General error in processing track {track['name']}: {ex}")

        return render_template('index.html', token=True, tracks=filtered_tracks)
    except Exception as e:
        print(f"Error during search: {e}")
        return "An error occurred during the search process. Please try again.", 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

def get_token():
    token_info = session.get('token_info', None)
    print(f"Token Info in get_token: {token_info}")  # Debug statement
    if not token_info:
        raise Exception("No token_info")

    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 60

    if is_expired:
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session['token_info'] = token_info

    return token_info

if __name__ == '__main__':
    app.run(debug=True)
