<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">
<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
<script type="text/javascript" src="http://mediaplayer.yahoo.com/latest"></script>
<title>Recommended MusicBrainz Album IDs</title>

</head>

<body>

<h1>Recommended MusicBrainz Album IDs</h1>

<form action="/resolve_submitalbums" method="post">
<span py:replace="mbrecommend_list(mbrecommend)"/>
<input type="submit" value="Process Checked Albums" />
</form>
</body>

</html>
