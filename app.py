#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
import json
import dateutil.parser
import babel
from flask import (
  Flask, render_template,
  request, Response, 
  flash, redirect,
  url_for)
from flask_moment import Moment
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler, error, exception
from flask_wtf import FlaskForm
from forms import *
from models import *
import sys

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database
SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:abcd@localhost:5432/fyyur_db'
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Custiomized Functions
#----------------------------------------------------------------------------#
def search(db_class, skey):
  data=[]
  results = db.session.query(db_class).filter(db_class.name.ilike(f'%{skey}%')|db_class.city.ilike(f'%{skey}%')|db_class.state.ilike(f'%{skey}%')).all()
  for result in results:
    data.append({
      "id": result.id,
      "name": result.name,
      "num_upcoming_shows": len(db.session.query(Show).filter(Show.venue_id == result.id).filter(Show.start_time > datetime.now()).all()),
    })
  results_data={
    "count": len(results),
    "data": data
  }
  return results_data

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')

#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  data = []
  groups = db.session.query(Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()
  if not groups: 
    flash('no venues exists') 
    return render_template('pages/venues.html')
  for group in groups:
    venues = db.session.query(Venue).filter_by(city=group[0], state=group[1]).all()
    venues_list = [] # a list containig all venues for each group
    for venue in venues:
      venues_list.append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": len(db.session.query(Show).filter(Show.venue_id == venue.id).filter(Show.start_time > datetime.now()).all())
      })
    data.append({
      "city":group[0],
      "state":group[1],
      "venues":venues_list,
    })
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  return render_template('pages/search_venues.html', results=search(Venue, request.form.get('search_term', '')), search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  v = Venue.query.get(venue_id)
  data = {
    "id": v.id,
    "name": v.name,
    "genres": v.genres,
    "address": v.address,
    "city": v.city,
    "state": v.state,
    "phone": v.phone,
    "website": v.website,
    "facebook_link": v.facebook_link,
    "seeking_talent": v.seeking_talent,
    "seeking_description": v.seeking_description,
    "image_link": v.image_link,
    "past_shows": [],
    "upcoming_shows": [],
    "past_shows_count": 0,
    "upcoming_shows_count": 0,
  }

  all_past_shows = db.session.query(Show).join(Venue).filter(Show.venue_id==venue_id).filter(Show.start_time<datetime.now()).all()
  past_shows_list = []

  for past_show in all_past_shows:
    past_shows_list.append({
      "artist_id": past_show.artist_id,
      "artist_name": past_show.artist.name,
      "artist_image_link": past_show.artist.image_link,
      "start_time": format_datetime(str(past_show.start_time))
    })

  data['past_shows'] = past_shows_list
  data['past_shows_count'] = len(past_shows_list)

  all_upcoming_shows = db.session.query(Show).join(Venue).filter(Show.venue_id==venue_id).filter(Show.start_time>datetime.now()).all()
  upcoming_shows_list = []

  for upcomming_show in all_upcoming_shows:
    upcoming_shows_list.append({
      "artist_id": upcomming_show.artist_id,
      "artist_name": upcomming_show.artist.name,
      "artist_image_link": upcomming_show.artist.image_link,
      "start_time": format_datetime(str(upcomming_show.start_time)) 
    })

  data['upcoming_shows'] = upcoming_shows_list
  data['upcoming_shows_count'] = len(upcoming_shows_list)

  return render_template('pages/show_venue.html', venue=data)

  
#  ----------------------------------------------------------------
@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  error = False
  try:

    new_venue = Venue(
      name=request.form['name'],
      genres=request.form.getlist('genres'),
      address=request.form['address'],
      city=request.form['city'],
      state=request.form['state'],
      phone=request.form['phone'],
      # website=request.form['website'],
      facebook_link=request.form['facebook_link'],
      #image_link=request.form['image_link'],
      # seeking_talent=request.form['seeking_talent'],
      # seeking_description=request.form['seeking_description'],
    )
    # insert new venue records into the db
    db.session.add(new_venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
    if error:
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    else:
      flash('Venue ' + request.form['name'] + ' was successfully listed!')

  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>/delete', methods=['POST'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  try:
    Venue_2b_deleted = db.session.query(Venue).filter_by(id=venue_id).first_or_404() 
    db.session.delete(Venue_2b_deleted)
    db.session.commit()
    flash('Venue is successfully deleted with all of its shows.')
  except:
    flash('Venue is not deleted, exception occurred!')
    db.session.rollback()
  finally:
    db.session.close()
  return redirect('/')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data = []
  artists = db.session.query(Artist).all()
  if not artists: 
    flash('no artists exists') 
    return render_template('pages/artists.html')
  for artist in artists:
    data.append({
      "id": artist.id,
      "name": artist.name,
      })
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  return render_template('pages/search_artists.html', results=search(Artist, request.form.get('search_term', '')), search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # TODO: replace with real artist data from the artist table, using artist_id
  a = Artist.query.get(artist_id)
  data = {
    "id": a.id,
    "name": a.name,
    "genres": a.genres,
    "city": a.city,
    "state": a.state,
    "phone": a.phone,
    "website": a.website,
    "facebook_link": a.facebook_link,
    "seeking_venue": a.seeking_venue,
    "seeking_description":a.seeking_description,
    "image_link": a.image_link,
    "past_shows": [],
    "upcoming_shows": [],
    "past_shows_count": 0,
    "upcoming_shows_count": 0,
  }
  
  all_past_shows = db.session.query(Show).join(Artist).filter(Show.artist_id==artist_id).filter(Show.start_time<datetime.now()).all()
  past_shows_list = []

  for past_show in all_past_shows:
    past_shows_list.append({
      "venue_id": past_show.venue_id,
      "venue_name": past_show.venue.name,
      "venue_image_link": past_show.venue.image_link,
      "start_time": format_datetime(str(past_show.start_time))
    })

  data['past_shows'] = past_shows_list
  data['past_shows_count'] = len(past_shows_list)

  all_upcoming_shows = db.session.query(Show).join(Artist).filter(Show.artist_id==artist_id).filter(Show.start_time>datetime.now()).all()
  upcoming_shows_list = []

  for upcomming_show in all_upcoming_shows:
    upcoming_shows_list.append({
      "venue_id": upcomming_show.venue_id,
      "venue_name": upcomming_show.venue.name,
      "venue_image_link": upcomming_show.venue.image_link,
      "start_time": format_datetime(str(upcomming_show.start_time))
      
    })

  data['upcoming_shows'] = upcoming_shows_list
  data['upcoming_shows_count'] = len(upcoming_shows_list)
  return render_template('pages/show_artist.html', artist=data)

#  Update 	
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.get_or_404(artist_id)
  if artist: 
    form = ArtistForm(obj=artist)
  else: flash('artist not found')
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  form = ArtistForm(request.form)
  try: 
    artist = Artist.query.get(artist_id)
    artist = form.populate_obj(artist)
    db.session.commit()
    flash('Successfully Updated!')  
  except: 
    flash('Ops! somthing went wrong the update was unsuccessful!')  
    db.session.rollback()
  finally: 
    db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get_or_404(venue_id)
  if venue: 
    form = VenueForm(obj=venue)
  else: flash('venue not found')
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  form = VenueForm(request.form)
  try: 
    venue = Venue.query.get(venue_id)
    venue = form.populate_obj(venue)
    db.session.commit()
    flash('Successfully Updated!') 
  except: 
    flash('Ops! somthing went wrong the update was unsuccessful!')  
    db.session.rollback()
  finally: 
    db.session.close()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist #
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET']) 
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  form = ArtistForm(request.form)
  name = form.name.data
  try:
     name_reserved = db.session.query(Artist).filter_by(name=name).first()
     if name_reserved: 
       flash('artist name reserved')
       return render_template('forms/new_artist.html',form=form)
     new_artist = Artist()
     form.populate_obj(new_artist)
     db.session.add(new_artist) 
     db.session.commit()
     # on successful db insert, flash success
     flash('Successfully listed!')
     return render_template('pages/home.html')  
  except:
    # TODO: on unsuccessful db insert, flash an error instead.
     flash('Could not be listed.')
     db.session.rollback()
     return render_template('forms/new_artist.html',form=form)
  finally:
     db.session.close()


#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue. #????
  data = []
  shows = db.session.query(Show).all()
  if not shows: 
    flash('no shows exists') 
    return render_template('pages/shows.html')
  for show in shows:
    data.append({
     "venue_id": show.venue_id,
     "venue_name": show.venue.name,
     "artist_id": show.artist_id,
     "artist_name": show.artist.name,
     "artist_image_link":show.artist.image_link,
     "start_time": str(show.start_time)
   })
  return render_template('pages/shows.html', shows=data)

  
@app.route('/shows/create') 
def create_shows():
  # renders form. do not touch. ----> OK :)
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    form = ShowForm(request.form)
    if form.validate():
        venue_id = form.venue_id.data
        artist_id = form.artist_id.data
        venue = db.session.query(Venue).filter_by(id=venue_id).first()
        artist = db.session.query(Artist).filter_by(id=artist_id).first()
        if not venue:
          flash("the Venue ID is wrong")
          return render_template('pages/new_show.html', form=form)
        if not artist:
          flash("the Artist ID is wrong")
          return render_template('pages/new_show.html', form=form)
        try:
          new_show = Show()
          form.populate_obj(new_show)
          db.session.add(new_show)
          db.session.commit()
          flash('Show was successfully listed!')
          return render_template('pages/show.html')
        except:
          db.session.rollback()
          flash('An error occurred. Show could not be listed.')
          return render_template('pages/new_show.html', form=form)
        finally:
          db.session.close() 
    else:
        msg = []
        for field, err in form.errors.items():
          msg.append(field + ' ' + '|'.join(err))
        flash('Errors ' + str(msg))
        return render_template('pages/new_show.html', form=form)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''