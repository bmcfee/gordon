<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">
<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
<title>Track <span py:replace="track.id"/></title>

<script type="text/javascript" src="http://mediaplayer.yahoo.com/js"></script>
</head>

<body>




<div class="main_content">        
<h3>Track <span py:replace="track.id"/>: <span py:replace="track.title"/><br/>
Main Artist: <span py:replace="track.artist"/><br/>
Album: <span py:replace="track.album"/> (Track <span py:replace="track.tracknum"/>, <span py:replace="track_time"/>)<br/>
MusicBrainz ID: <span py:replace="track.mb_id"/><br/>
</h3>
<hr/>


<a title="${track.artist} - ${track.title} (${track.album})" href="/audio/T${track.id}.${track.fn_audio_extension}"></a>|
<span py:for="a in alternate_action">
<span py:content="a">X</span> |
<a href="/download/track_id:${track.id}">Download</a>|
</span>
| <span py:replace="track_mb_id_link"/> |   

<!--span py:replace="yahoo_url"/-->

<a href="/playlist?params=track_id:${track.id}" type="application/xspf+xml"></a>
<hr/>

<table>
<tr>
<td><span py:replace="afeat_graph"/></td>
<td>
<span py:for="f in feat_urllist">
<span py:content="f">X</span><br/>
</span>
</td>
</tr>
</table>


<hr/>
<span py:replace="track_widget(track_widget_data)"/>
<span py:replace="artist_widget(artists)"/>
<span py:replace="album_widget(albums)"/>



<hr/>


</div>


</body>

</html>
