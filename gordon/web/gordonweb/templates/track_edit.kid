<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">
<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
<title>Modify Track <span py:replace="track.id">ID</span></title>
</head>

<body>

<div class="main_content">        

<h3>Track <span py:replace="track.id">ID</span></h3>

<span py:replace="track_edit_widget(track)"/>

<br/>            


</div>


</body>

</html>
