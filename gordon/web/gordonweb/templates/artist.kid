<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">
<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
<title>Artist: <div py:replace="artist.name">Name goes here</div></title>


<script type="text/javascript" src="http://mediaplayer.yahoo.com/js"></script>
</head>

<body>

<div class="main_content">        

<h3>
Artist <span py:replace="artist.id"/>: <span py:replace="artist.name"/><br/>
MusicBrainz ID: <span py:replace="artist.mb_id"/><br/>
</h3>
<hr/>
<span py:replace="alternate_action"/> |
<span py:replace="artist_mb_id_link"/> |


<!-- <a href="/playlist?params=artist_id:${artist.id}!randomize:1" type="application/xspf+xml"></a> -->
(Reload to reshuffle) 
<!-- We always randomize artists.... want something in order, go to the album!<a href="/artist/${artist.id}/${action}/shuffle">Reshuffle</a>--> 

<!--
<table>
<tr>
<td><span py:replace="artist_top_sim_datagrid(artist_top_sims)"/></td>
<td>&nbsp;</td>
<td>&nbsp;</td>
<td>&nbsp;</td>
<td><span py:replace="artist_bottom_sim_datagrid(artist_bottom_sims)"/></td>
</tr>
</table>
<hr/>
-->


<span py:replace="artist_widget(artist_widget_data)"/>
<span py:replace="album_widget(albums)"/>


<span py:for="m in mp3s">
<span py:content="m">X</span>
</span>


</div>


</body>

</html>
