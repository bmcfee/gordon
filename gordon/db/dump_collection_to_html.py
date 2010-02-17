import gordon_db

artists = gordon.db.Artist.query.order_by('name')

for artist in artists :
    for album in artist.albums:
        albumname = 'Unknown Album' if len(album.name)==0 else album.name
        st='%s -- %s (%i tracks)' % (artist.name,albumname,album.trackcount)
        if len(artist.name)>0 :
            print st.encode('utf-8')
