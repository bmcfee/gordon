<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">
<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
<title>Collection <div py:replace="collection.id">ID goes here</div></title>
<script type="text/javascript" src="http://mediaplayer.yahoo.com/latest"></script>
</head>



<body>

<div class="main_content">     


<table>
<tr><td>
</td>
<td>
<h3>Collection <span py:replace="collection.id"/>: <span py:replace="collection.name"/><br/>
Trackcount: <span py:replace="collection.trackcount"/><br/>
Description:</h3> <span py:replace="collection.description"/><br/>
</td></tr>
</table>

<a href="/collection/${collection.id}/${action}/shuffle">Shuffle</a>
<a href="/download/collection_id:${collection.id}">Download</a>
<hr/>

<span py:replace="track_datagrid(tracks)"/>


</div>


</body>

</html>
