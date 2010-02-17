<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">
<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
<title>Album <div py:replace="album.id">ID goes here</div></title>
<script type="text/javascript" src="http://mediaplayer.yahoo.com/latest"></script>
</head>



<body>

<div class="main_content">     


<table>
<tr><td>
<div py:replace="albumcover">Text goes here</div>
</td>
<td>
<h3>Album <span py:replace="album.id"/>: <span py:replace="album.name"/><br/>
Artist(s): <span py:replace="artiststring"/><br/>
Trackcount: <span py:replace="album.trackcount"/><br/>
MusicBrainz ID: <span py:replace="album.mb_id"/><br/></h3>
</td></tr>
</table>


<hr/>


<table border="1">
<tr py:if="do_albumgrid">
<td py:for="i in range(3)">
  <center>
    <span py:replace="top_albumcovers[i]"/><br/>
    <font size="-4">
      <span py:replace="top_albumartists[i]"/><br/>
      <span py:replace="top_albumtitles[i]"/>
    </font>
  </center>
</td>
</tr>

<tr py:if="do_albumgrid">
<td>
<center>
  <span py:replace="top_albumcovers[3]"/><br/>
  <font size="-4">
    <span py:replace="top_albumartists[3]"/><br/>
    <span py:replace="top_albumtitles[3]"/>
  </font>
</center>
</td>
<td>
<center>
  <span py:replace="albumcover"/><br/>
</center>
</td>
<td>
<center>
  <span py:replace="top_albumcovers[4]"/><br/>
  <font size="-4">
    <span py:replace="top_albumartists[4]"/><br/>
    <span py:replace="top_albumtitles[4]"/>
  </font>
</center>
</td>
</tr>


<tr>
<td py:if="do_albumgrid" py:for="i in range(6,9)">
  <center>
    <span py:replace="top_albumcovers[i-1]"/><br/>
    <font size="-4">
      <span py:replace="top_albumartists[i-1]"/><br/>
      <span py:replace="top_albumtitles[i-1]"/>
    </font>
  </center>
</td>


<span py:replace="alternate_action"/>
<a href="/album/${album.id}/${action}/shuffle">Shuffle</a>
<a href="/download/album_id:${album.id}">Download</a>
<a href="/resolve_viewalbum/${album.id}">MB Resolve</a>
<span py:replace="album_mb_id_link"/>
<hr/>
   
<span py:replace="album_widget(album_widget_data)"/>
<span py:replace="artist_widget(artists)"/>


<form method="post" action="/album_modify">
 <input id="form_id" type="hidden" name="id" value="${album.id}" class="hiddenfield"/>     
 <input id="form_operation" type="hidden" name="operation" value="deletetracks" class="hiddenfield"/>     
 <input id="form_referer" type="hidden" name="referer" value="${album.referer}" class="hiddenfield"/>     
 <span py:replace="track_widget(tracks)"/>
 <span py:replace="deleteform_button"/>
</form>


<p py:if="do_albumgrid"><hr/></p><hr/>

</tr>
</table>

<table>
<tr>
<td><span py:if="do_albumgrid" py:replace="album_top_sim_datagrid(album_top_sims)"/></td>
<td>&nbsp;</td>
<td>&nbsp;</td>
<td>&nbsp;</td>
<td><span py:if="do_albumgrid" py:replace="album_bottom_sim_datagrid(album_bottom_sims)"/></td>
</tr>
</table>



</div>


</body>

</html>
