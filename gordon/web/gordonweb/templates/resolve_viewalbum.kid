<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">
<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
<title>Resolve Album <div py:replace="album.id">ID goes here</div></title>

<script type="text/javascript" src="http://mediaplayer.yahoo.com/latest"></script>

</head>



<body>

<div class="main_content">        

<table>
<tr><td>
<div py:replace="albumcover">Text goes here</div>
</td>
<td>
<font size="+1">Existing Album: <div py:replace="album.name">Album name goes here</div></font><br />
<font size="+1">Existing Artist(s): <div py:replace="artiststring">Artist name goes here</div></font><br />
ID: <div py:replace="album.id">ID goes here</div><br />
Existing MB_ID: <div py:replace="album.mb_id">MB_ID goes here</div><br />
Recommended MB_ID: <div py:replace="mbrecommend_mb_id_url">URL Goes here</div><br />

Confidence: <div py:replace="mbrecommend.conf">Conf here</div> 
(artist=<div py:replace="mbrecommend.conf_artist">Conf here</div>,
album=<div py:replace="mbrecommend.conf_album">Conf here</div>,
track=<div py:replace="mbrecommend.conf_track">Conf here</div>,
time=<div py:replace="mbrecommend.conf_time">Conf here</div>)<br />
&nbsp;<br /> 

<a href="/resolve_recommendalbum/${album.id}">Redo Recomendation</a>
<a href="/resolve_setalbumstatus/${album.id}?status=weird">Mark as Weird</a>
<a href="/album/${album.id}/edit">Edit</a>

${submit_form.display()}
</td></tr>
</table>

<font size="+1">Recommended Album: <div py:replace="mb_album">Album name goes here</div></font><br />
<span py:replace="tracklist(tracks)"/>


</div>


</body>

</html>
