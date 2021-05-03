from flask import Flask, request, jsonify, Response, abort
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from base64 import b64encode
import os 


#Init app
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

#Datanase
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#Init db
db = SQLAlchemy(app)

#Init ma
ma = Marshmallow(app)

#Artist Model/Class
class Artist(db.Model):
    id = db.Column(db.String(200), primary_key=True)
    name = db.Column(db.String(200))
    age = db.Column(db.Integer)
    albums = db.Column(db.String(200))
    tracks = db.Column(db.String(200))
    self = db.Column(db.String(200))


    def __init__(self, id, name, age, albums, tracks, artist_self):
        self.id = id
        self.name = name
        self.age = age
        self.albums = albums
        self.tracks = tracks
        self.self = artist_self

#Artist Schema
class ArtistSchema(ma.Schema):
    class Meta: 
        fields = ('id', 'name', 'age', 'albums', 'tracks', 'self')

#Init schema
artist_schema = ArtistSchema()
artists_schema = ArtistSchema(many=True)

#Create Artist
@app.route('/artists', methods=['POST'])
def add_artist():
    try:
        name =  request.json['name']
        age = request.json['age']
    except: 
        return Response(status=400)

    if not isinstance(name, str) or not isinstance(age, int): 
        return Response(status=400)

    id = b64encode(name.encode()).decode('utf-8')[0:21]
    albums = f'https://iic3103-2.herokuapp.com/artists/{id}/albums'
    tracks = f'https://iic3103-2.herokuapp.com/artists/{id}/tracks'
    self = f'https://iic3103-2.herokuapp.com/artists/{id}'
    if Artist.query.get(id): 
        artist = Artist.query.get(id)
        return artist_schema.jsonify(artist), 409

    else: 
        new_artist = Artist(id, name, age, albums, tracks, self)
        db.session.add(new_artist)
        db.session.commit()
    return artist_schema.jsonify(new_artist), 201

#Get all artists
@app.route('/artists', methods=['GET'])
def get_artists():
    all_artists = Artist.query.all()
    result = artists_schema.dump(all_artists)
    return jsonify(result), 200

#Get artist
@app.route('/artists/<artist_id>', methods=['GET'])
def get_artist(artist_id):
    try:
        artist = Artist.query.get(artist_id)
    except: 
        return Response(status=404)
    return artist_schema.jsonify(artist), 200

#Get artist's albums
@app.route('/artists/<artist_id>/albums', methods=['GET'])
def get_artist_albums(artist_id):
    try:
        artist = Artist.query.get(artist_id)
    except: 
        return Response(status=404)
    albums = Album.query.filter_by(artist_id=artist_id).all()
    result = albums_schema.dump(albums)
    return jsonify(result), 200

#Get artist's tracks
@app.route('/artists/<artist_id>/tracks', methods=['GET'])
def get_artist_tracks(artist_id):
    try:
        artist = Artist.query.get(artist_id)
    except: 
        return Response(status=404)
    artist_url = Artist.query.filter_by(id = artist_id).first()
    artist_url_self= artist_url.self
    tracks = Track.query.filter_by(artist=artist_url_self).all()
    result = tracks_schema.dump(tracks)
    return jsonify(result), 200

#Play artist
@app.route('/artists/<artist_id>/albums/play', methods=['PUT'])
def play_artist(artist_id):
    try:
        artist = Artist.query.get(artist_id)
        artist_url_self= artist.self
        tracks = Track.query.filter_by(artist = artist_url_self).all()
        result = tracks_schema.dump(tracks)
    except: 
        return Response(status=404)
    #artist_url = Artist.query.filter_by(id = artist_id).first()
    #artist_url_self= artist_url.self
    for track in result:
        track = Track.query.get(track['id'])
        track.times_played += 1
    db.session.commit()
    return Response(status=200)

#Delete artist
@app.route('/artists/<artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
    try:
        artist = Artist.query.get(artist_id)
    except: 
        return Response(status=404)
    artist = Artist.query.get(artist_id)
    albums = Album.query.filter_by(artist = artist.self).all()
    result= albums_schema.dump(albums)
    for album in result:
        album = Album.query.get(album['id'])
        tracks = Track.query.filter_by(album_id = album.id)
        result_tracks = tracks_schema.dump(tracks)
        for track in result_tracks:
            track = Track.query.get(track['id'])
            db.session.delete(track)
        db.session.delete(album)
    db.session.delete(artist)
    db.session.commit()

    return Response(status=204)


#Album Model/Class
class Album(db.Model):
    id = db.Column(db.String(200), primary_key=True)
    artist_id = db.Column(db.String(200), db.ForeignKey('artist.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(200))
    genre = db.Column(db.String(200))
    artist = db.Column(db.String(200))
    tracks = db.Column(db.String(200))
    self = db.Column(db.String(200))


    def __init__(self, id, name, artist_id, genre, artist, tracks, album_self):
        self.id = id
        self.name = name
        self.artist_id = artist_id
        self.genre = genre
        self.artist = artist
        self.tracks = tracks
        self.self = album_self

#Album Schema
class AlbumSchema(ma.Schema):
    class Meta: 
        fields = ('id', 'name', 'artist_id', 'genre', 'artist', 'tracks', 'self')

#Init schema
album_schema = AlbumSchema()
albums_schema = AlbumSchema(many=True)

#Create Album
@app.route('/artists/<artist_id>/albums', methods=['POST'])
def add_album(artist_id):
    try:
        name =  request.json['name']
        genre = request.json['genre']
        id = b64encode(name.encode()).decode('utf-8')[0:21]
    except: 
        return Response("{'code': 400, 'description': 'input invalido'}", status=400)
     
    try: 
        artist = Artist.query.get(artist_id)
    except: 
        return Response("{'code': 422, 'description': 'artista no existe'}", status=422)

    if Album.query.get(id):
        album = Album.query.get(id)
        data = {'code': 409, 'description':'album ya existe', 'body':{'id': album.id, 'name': album.name, 'artist_id': album.artist_id, 'genre': album.genre, 'artist': album.artist, 'tracks': album.tracks, 'self': album.self}}
        return jsonify(data), 409

    if not isinstance(name, str) or not isinstance(genre, str): 
        return Response("{'code': 400, 'description': 'input invalido'}", status=400)
    artist_id = artist_id
    artist = f'https://iic3103-2.herokuapp.com/artists/{artist_id}'
    tracks = f'https://iic3103-2.herokuapp.com/albums/{id}/tracks'
    self = f'https://iic3103-2.herokuapp.com/albums/{id}'

    new_album = Album(id, name, artist_id, genre, artist, tracks, self)

    db.session.add(new_album)
    db.session.commit()
    data = {'code': 201, 'description':'album creado', 'body':{'id': new_album.id, 'name': new_album.name, 'artist_id': new_album.artist_id, 'genre': new_album.genre, 'artist': new_album.artist, 'tracks': new_album.tracks, 'self': new_album.self}}
    return jsonify(data), 201

#Get all albums
@app.route('/albums', methods=['GET'])
def get_albums():
    all_albums = Album.query.all()
    result = albums_schema.dump(all_albums)
    data = {'code': 200, 'description':'resultados obtenidos', 'body': result}
    return jsonify(data), 200

#Get album
@app.route('/albums/<album_id>', methods=['GET'])
def get_album(album_id):
    try:
        album = Album.query.get(album_id)
    except: 
        return Response("{'code': 404, 'description': 'álbum no encontrado'}", status=404)
    data = {'code': 200, 'description':'operación exitosa', 'body':{'id': album.id, 'name': album.name, 'artist_id': artist_id, 'genre': album.genre, 'artist': album.artist, 'tracks': album.tracks, 'self': album.self}}
    return jsonify(data), 200

#Get album's tracks
@app.route('/albums/<album_id>/tracks', methods=['GET'])
def get_albums_tracks(album_id):
    try: 
        album = Album.query.get(album_id)
    except: 
        return Response("{'code': 404, 'description': 'álbum no encontrado'}", status=404)
    tracks = Track.query.filter_by(album_id=album_id)
    result = tracks_schema.dump(tracks)
    data = {'code': 200, 'description':'resultados obtenidos', 'body': result}
    return jsonify(data), 200

#Play album
@app.route('/albums/<album_id>/tracks/play', methods=['PUT'])
def play_album(album_id):
    if Album.query.get(album_id) == None:
        album = Album.query.get(album_id)
        tracks = Track.query.filter_by(album_id = album_id).all()
        result = tracks_schema.dump(tracks)
        for track in result:
            track = Track.query.get(track['id'])
            track.times_played += 1
        db.session.commit()
        return Response("{'code': 404, 'description': 'álbum no encontrado'}", status=404)
        
    else: 
        return Response("{'code': 200, 'description': 'canciones del álbum reproducidas'}", status=200)
        
    
    

#Delete album
@app.route('/albums/<album_id>', methods=['DELETE'])
def delete_album(album_id):
    try: 
        album = Album.query.get(album_id)
    except: 
        return Response("{'code': 404, 'description':'álbum no encontrado'}", status=404)
    tracks = Track.query.filter_by(album_id = album_id).all()
    result = tracks_schema.dump(tracks)
    for track in result:
        track = Track.query.get(track['id'])
        db.session.delete(track)
    db.session.delete(album)
    db.session.commit()

    return Response("{'code': 204, 'description': 'álbum eliminado'}", status=204)



#Track Model/Class
class Track(db.Model):
    id = db.Column(db.String(200), primary_key=True)
    album_id = db.Column(db.String(200), db.ForeignKey('album.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(200))
    duration = db.Column(db.Float)
    times_played = db.Column(db.Integer)
    artist = db.Column(db.String(200))
    album = db.Column(db.String(200))
    self = db.Column(db.String(200))


    def __init__(self, id, album_id, name, duration, times_played, artist, album, track_self):
        self.id = id
        self.album_id = album_id
        self.name = name
        self.duration = duration
        self.times_played = times_played
        self.artist = artist
        self.album = album
        self.self = track_self

#Track Schema
class TrackSchema(ma.Schema):
    class Meta: 
        fields = ('id', 'album_id', 'name', 'duration', 'times_played', 'artist', 'album', 'self')

#Init schema
track_schema = TrackSchema()
tracks_schema = TrackSchema(many=True)

#Create Track
@app.route('/albums/<album_id>/tracks', methods=['POST'])
def add_track(album_id):
    try: 
        name = request.json['name']
        duration = request.json['duration']
        id = b64encode(name.encode()).decode('utf-8')[0:21]
    except: 
        return Response("{'code': 400, 'description': 'input invalido'}", status=400)
    
    try: 
        album = Album.query.get(album_id)
    except: 
        return Response("{'code': 422, 'description': 'álbum no existe'}", status=422)
    
    if Track.query.get(id):
        track = Track.query.get(id)
        data = {'code': 409, 'description':'canción ya existe', 'body':{'id': track.id, 'album_id': track.album_id, 'name': track.name, 'duration': track.duration, 'times_played': track.times_played, 'artist': track.artist, 'album': track.album, 'self': track.self}}
        return jsonify(data), 409

    if not isinstance(name, str) or not isinstance(duration, float): 
        return Response("{'code': 400, 'description': 'input invalido'}", status=400)

    album_id = album_id
    times_played = 0
    artist_id = Album.query.filter_by(id =album_id).first()
    artist = f'https://iic3103-2.herokuapp.com/artists/{artist_id.artist_id}'
    album = f'https://iic3103-2.herokuapp.com/albums/{album_id}'
    self = f'https://iic3103-2.herokuapp.com/tracks/{id}'

    new_track = Track(id, album_id, name, duration, times_played, artist, album, self)

    db.session.add(new_track)
    db.session.commit()

    data = {'code': 201, 'description':'canción creada', 'body':{'id': new_track.id, 'album_id': new_track.album_id, 'name': new_track.name, 'duration': new_track.duration, 'times_played': new_track.times_played, 'artist': new_track.artist, 'album': new_track.album, 'self': new_track.self}}
    return jsonify(data), 201

#Get all tracks
@app.route('/tracks', methods=['GET'])
def get_tracks():
    all_tracks = Track.query.all()
    result = tracks_schema.dump(all_tracks)
    data = {'code': 200, 'description':'operación exitosa', 'body': result}
    return jsonify(data), 200

#Get track
@app.route('/tracks/<track_id>', methods=['GET'])
def get_track(track_id):
    try: 
        track = Track.query.get(track_id)
    except: 
        return Response("{'code': 404, 'description': 'Canción no encontrada'}", status=404)
    
    data = {'code': 200, 'description':'operación exitosa', 'body':{'id': track.id, 'album_id': track.album_id, 'name': track.name, 'duration': track.duration, 'times_played': track.times_played, 'artist': track.artist, 'album': track.album, 'self': track.self}}
    return jsonify(data), 200

#Put track
@app.route('/tracks/<track_id>/play', methods=['PUT'])
def play_track(track_id):
    try: 
        track = Track.query.get(track_id)
        track.times_played += 1
    except: 
        return Response("{'code': 404, 'description': 'canción no encontrada'}", status=404)
    db.session.commit()
    return Response("{'code': 200, 'description': 'canción reproducida'}", status=200)
    

#Delete track
@app.route('/tracks/<track_id>', methods=['DELETE'])
def delete_track(track_id):
    try: 
        track = Track.query.get(track_id)
    except: 
        return Response("{'code': 404, 'description':'canción inexistente'}", status=404)
    db.session.delete(track)
    db.session.commit()

    return Response(status=204)




