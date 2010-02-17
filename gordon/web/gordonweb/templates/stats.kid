<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">
<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
<title>Statistics</title>
</head>

<body>

<div class="main_content">        

<h1>Statistics</h1>


<h2>Useful statistics</h2>
<table>
<tr> <th></th><th>Total</th><th>Labeled</th></tr>
<tr> <td>Artists</td> <td><span py:replace="artist_total"/> </td> <td> <span py:replace="artist_labeled"/> (<span py:replace="artist_pct"/>)</td> </tr>
<tr> <td>Albums</td> <td><span py:replace="album_total"/> </td> <td> <span py:replace="album_labeled"/> (<span py:replace="album_pct"/>)</td> </tr>
<tr> <td>Tracks</td> <td><span py:replace="track_total"/> </td> <td> <span py:replace="track_labeled"/> (<span py:replace="track_pct"/>)</td> </tr>
</table>
<p/>


<h2>Useless statistics</h2>
Seconds of audio: <span py:replace="sec_total"/><br/>
Or <span py:replace="time_total"/><br/>

</div>


</body>

</html>
